#!/usr/bin/env python
"""Report dead templates, dead endpoints and broken HTMX wiring.

Run with `just deadcode`. Nothing here is hooked into prek.

How it works
------------
ast-grep cannot parse Jinja. A single ``{% extends %}`` at the top of a file
collapses the entire document into ``ERROR`` nodes, so no ``element`` or
``attribute`` node ever matches. So templates are rewritten into a throwaway
HTML mirror first:

* ``{{ expr }}`` becomes the literal value when ``expr`` resolves to a
  ``{% set %}`` constant, otherwise the sentinel ``@@``.
* ``{% ... %}`` and ``{# ... #}`` are blanked out to spaces.

Newlines are preserved, so mirror line numbers match the source exactly and
the generated mirror is easy to eyeball when a finding looks wrong.

The mirror is generated once per page template using that page's include
closure, because the same partial can resolve differently depending on which
page pulls it in (``shared/_pagination.jinja2`` is the obvious example).

Facts are collected by the rules in ``rules/``; everything cross-file -- set
arithmetic over template names, DOM ids and URLs -- happens here.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TEMPLATES = ROOT / "src" / "pipances" / "templates"
STATIC_JS = ROOT / "static" / "js" / "pages"
TESTS = ROOT / "tests"
CONFIG = HERE / "sgconfig.yml"

#: Placeholder for a value that came from Jinja and could not be resolved.
DYNAMIC = "@@"

#: Routes that are navigated to directly rather than linked from markup.
ENTRY_POINTS = {"/"}

JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
JINJA_EXPR = re.compile(r"\{\{.*?\}\}", re.S)
JINJA_TAG = re.compile(r"\{%.*?%\}", re.S)
JINJA_SET = re.compile(r"\{%-?\s*set\s+(\w+)\s*=\s*(.*?)\s*-?%\}", re.S)
JINJA_REF = re.compile(
    r"""\{%-?\s*(?:include|extends|import|from)\s+["']([^"']+\.jinja2)["']"""
)
JINJA_MACRO = re.compile(r"\{%-?\s*macro\s+(\w+)\s*\(")
PY_TEMPLATE = re.compile(r"""["']([A-Za-z0-9_/]+\.jinja2)["']""")
SCRIPT_BLOCK = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
QUOTED = re.compile(r"""^(['"])(.*)\1$""", re.S)

#: `hx-*` attribute -> HTTP method, for URL cross-checking.
METHOD_OF = {
    "hx-get": "GET",
    "hx-post": "POST",
    "hx-put": "PUT",
    "hx-patch": "PATCH",
    "hx-delete": "DELETE",
    "href": "GET",
    "src": "GET",
    "action": "POST",
}


# --------------------------------------------------------------------------
# Jinja -> HTML mirror
# --------------------------------------------------------------------------


def strip_jinja(
    text: str, literals: dict[str, str], candidates: dict[str, set[str]]
) -> str:
    """Blank Jinja syntax, substituting resolvable ``{% set %}`` constants.

    A ``{{ name }}`` that does not resolve here but is a known context
    variable is kept as the marker ``@@name@@``, so it can be expanded into its
    candidate values during analysis. Everything else becomes ``@@``.
    """
    text = JINJA_COMMENT.sub(_blank, text)
    text = JINJA_EXPR.sub(lambda m: _expression(m.group(0), literals, candidates), text)
    return JINJA_TAG.sub(_blank, text)


def _expression(
    token: str, literals: dict[str, str], candidates: dict[str, set[str]]
) -> str:
    inner = token[2:-2].strip()
    if inner in literals:
        return literals[inner]
    if re.fullmatch(r"\w+", inner) and inner in candidates:
        return f"@@{inner}@@"
    return DYNAMIC


def _blank(match: re.Match[str]) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in match.group(0))


def _constant(expr: str, known: dict[str, str]) -> str | None:
    """Evaluate a Jinja expression that is only literals and ``~`` concat."""
    expr = expr.strip()
    if quoted := QUOTED.match(expr):
        return quoted.group(2)
    if re.fullmatch(r"\d+", expr):
        return expr
    if re.fullmatch(r"\w+", expr):
        return known.get(expr)
    parts = [p.strip() for p in expr.split("~")]
    if len(parts) > 1:
        values = [_constant(p, known) for p in parts]
        if all(v is not None for v in values):
            return "".join(v for v in values if v is not None)
    return None


def local_literals(sources: dict[str, str]) -> dict[str, dict[str, str]]:
    """Per-file ``{% set name = <constant> %}`` values.

    A name is only resolved when every assignment in the file agrees and none
    of them is a self-assignment such as ``{% set pagination_id = pagination_id %}``,
    which would otherwise leak one page's value into another.
    """
    result: dict[str, dict[str, str]] = {}
    for name, text in sources.items():
        assigns: dict[str, list[str]] = defaultdict(list)
        for match in JINJA_SET.finditer(text):
            assigns[match.group(1)].append(match.group(2))
        resolved: dict[str, str] = {}
        for _ in range(4):
            changed = False
            for var, exprs in assigns.items():
                if var in resolved:
                    continue
                values = {v for e in exprs if (v := _constant(e, resolved)) is not None}
                if len(values) == 1:
                    resolved[var] = values.pop()
                    changed = True
            if not changed:
                break
        result[name] = resolved
    return result


def _literal_pairs(node: ast.AST) -> dict[str, str]:
    """String keys mapped to string values in a dict literal."""
    if not isinstance(node, ast.Dict):
        return {}
    pairs = {}
    for key, value in zip(node.keys, node.values, strict=True):
        if (
            isinstance(key, ast.Constant)
            and isinstance(key.value, str)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            pairs[key.value] = value.value
    return pairs


def context_literals() -> dict[str, set[str]]:
    """Candidate values for context variables that Python passes to templates.

    Only dict literals that reach a ``render(...)`` / ``TemplateResponse(...)``
    call count, either inline or through a name assigned in the same function
    (``ctx = {...}``, ``ctx |= {...}``, ``ctx.update({...})``). That is how the
    routes here pass context, and it is what lets the checker see that
    ``pagination_id`` can be ``explore-pagination`` as well as
    ``inbox-pagination``.
    """
    found: dict[str, set[str]] = defaultdict(set)
    for path in sorted((ROOT / "src" / "pipances").rglob("*.py")):
        for fn in ast.walk(ast.parse(path.read_text())):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            local: dict[str, dict[str, str]] = defaultdict(dict)
            for node in ast.walk(fn):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            local[target.id].update(_literal_pairs(node.value))
                elif (
                    isinstance(node, ast.AugAssign)
                    and isinstance(node.target, ast.Name)
                    and isinstance(node.value, ast.Dict)
                ):
                    local[node.target.id].update(_literal_pairs(node.value))
                elif (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "update"
                    and isinstance(node.func.value, ast.Name)
                    and node.args
                ):
                    local[node.func.value.id].update(_literal_pairs(node.args[0]))
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                called = (
                    node.func.attr if isinstance(node.func, ast.Attribute) else None
                )
                if called not in ("render", "TemplateResponse"):
                    continue
                for arg in node.args:
                    if isinstance(arg, ast.Dict):
                        pairs = _literal_pairs(arg)
                    elif isinstance(arg, ast.Name):
                        pairs = local.get(arg.id, {})
                    else:
                        pairs = {}
                    for key, value in pairs.items():
                        found[key].add(value)
    return found


def all_candidates(local: dict[str, dict[str, str]]) -> dict[str, set[str]]:
    """Every literal a name may hold, from Python context and ``{% set %}``."""
    merged: dict[str, set[str]] = defaultdict(set, context_literals())
    for mapping in local.values():
        for name, value in mapping.items():
            merged[name].add(value)
    return merged


MARKER = re.compile(r"@@([A-Za-z_]\w*)@@")
EXPANSION_LIMIT = 500


def expand(value: str, candidates: dict[str, set[str]]) -> set[str]:
    """Expand ``@@name@@`` markers into the literals ``name`` may hold.

    Returns an empty set when a marker cannot be resolved, so callers can tell
    "no candidates" apart from "no markers".
    """
    chunks = MARKER.split(value)
    if len(chunks) == 1:
        return {value}
    out = {chunks[0]}
    for i in range(1, len(chunks), 2):
        values = candidates.get(chunks[i])
        if not values:
            return set()
        out = {prefix + v + chunks[i + 1] for prefix in out for v in values}
        if len(out) > EXPANSION_LIMIT:
            return set()
    return out


def collapse_markers(value: str) -> str:
    """Reduce ``@@name@@`` back to a plain ``@@`` wildcard."""
    return MARKER.sub(DYNAMIC, value)


def include_edges(sources: dict[str, str]) -> dict[str, set[str]]:
    return {name: set(JINJA_REF.findall(text)) for name, text in sources.items()}


def closure(page: str, edges: dict[str, set[str]]) -> list[str]:
    seen: set[str] = set()
    order: list[str] = []
    stack = [page]
    while stack:
        name = stack.pop()
        if name in seen or name not in edges:
            continue
        seen.add(name)
        order.append(name)
        stack.extend(sorted(edges[name]))
    return order


@dataclass
class Mirror:
    """A generated file, and how to get back to the template it came from."""

    source: str
    offset: int = 0


def build_mirror(
    root: Path,
    sources: dict[str, str],
    literals: dict[str, dict[str, str]],
    candidates: dict[str, set[str]],
    edges: dict[str, set[str]],
    pages: list[str],
) -> dict[str, Mirror]:
    index: dict[str, Mirror] = {}
    for page in pages:
        order = closure(page, edges)
        merged: dict[str, str] = {}
        for name in reversed(order):  # deepest first, page wins
            merged.update(literals[name])
        stem = page.replace("/", "__").removesuffix(".jinja2")
        page_dir = root / stem
        page_dir.mkdir(parents=True, exist_ok=True)
        for name in order:
            stripped = strip_jinja(sources[name], merged, candidates)
            flat = name.replace("/", "__")
            html_path = page_dir / f"{flat}.html"
            html_path.write_text(stripped)
            index[str(html_path)] = Mirror(name)
            for i, match in enumerate(SCRIPT_BLOCK.finditer(stripped)):
                if "src=" in match.group(1).lower() or not match.group(2).strip():
                    continue
                js_path = page_dir / f"{flat}.script{i}.js"
                js_path.write_text(match.group(2))
                index[str(js_path)] = Mirror(
                    name, stripped.count("\n", 0, match.start(2))
                )

    static_dir = root / "_static"
    for path in sorted(STATIC_JS.rglob("*.js")):
        # only hand-written page scripts; static/js/external is vendored
        target = static_dir / path.relative_to(STATIC_JS)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        index[str(target)] = Mirror(str(path.relative_to(ROOT)))
    return index


# --------------------------------------------------------------------------
# ast-grep
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Hit:
    source: str
    line: int
    rule: str
    attr: str
    value: str

    def where(self) -> str:
        return f"{self.source}:{self.line}"


def scan(mirror_dir: Path, index: dict[str, Mirror]) -> list[Hit]:
    exe = shutil.which("ast-grep")
    if exe is None:
        sys.exit("ast-grep not found on PATH -- run this inside `nix develop`")
    proc = subprocess.run(
        [exe, "scan", "-c", str(CONFIG), "--json=compact", str(mirror_dir)],
        capture_output=True,
        text=True,
    )
    try:
        findings = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        sys.exit(f"ast-grep produced no JSON:\n{proc.stdout}\n{proc.stderr}")

    hits: list[Hit] = []
    for entry in findings:
        mirror = index.get(str(Path(entry["file"]).resolve()))
        if mirror is None:
            continue
        single = entry.get("metaVariables", {}).get("single", {})
        value = single.get("VAL", {}).get("text", entry["text"]).strip()
        attr = entry["text"].split("=", 1)[0].strip()
        hits.append(
            Hit(
                source=mirror.source,
                line=entry["range"]["start"]["line"] + mirror.offset + 1,
                rule=entry["ruleId"],
                attr=attr,
                value=value.strip("\"'`"),
            )
        )
    # The same partial is mirrored once per page, so collapse duplicates.
    return sorted(set(hits), key=lambda h: (h.source, h.line, h.rule, h.value))


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Route:
    path: str
    methods: frozenset[str]
    handler: str
    file: str


def collect_routes() -> list[Route]:
    from starlette.routing import Route as StarletteRoute

    from pipances.main import app

    routes = []
    for route in app.routes:
        if not isinstance(route, StarletteRoute):
            continue
        if not getattr(route.endpoint, "__module__", "").startswith("pipances"):
            continue
        routes.append(
            Route(
                path=route.path,
                methods=frozenset((route.methods or set()) - {"HEAD"}),
                handler=getattr(route.endpoint, "__name__", repr(route.endpoint)),
                file=str(
                    Path(inspect.getsourcefile(route.endpoint) or "?").relative_to(ROOT)
                ),
            )
        )
    return sorted(routes, key=lambda r: (r.path, sorted(r.methods)))


def segments(path: str) -> list[str]:
    path = path.split("?")[0].split("#")[0]
    return [s for s in path.strip("/").split("/") if s]


def route_matches(route_path: str, url: str) -> bool:
    """Match a URL against a route path, treating ``{param}`` and ``@@`` as wildcards."""
    route, want = segments(route_path), segments(url)
    if len(route) == len(want):
        return all(
            seg.startswith("{") or seg == w or w == DYNAMIC
            for seg, w in zip(route, want, strict=True)
        )
    if len(want) < len(route):
        # A JS string concatenation such as "/api/categories/" + id.
        return all(
            seg == w or w == DYNAMIC for seg, w in zip(route, want, strict=False)
        ) and all(seg.startswith("{") for seg in route[len(want) :])
    return False


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


@dataclass
class Report:
    orphan_templates: list[str] = field(default_factory=list)
    broken_template_refs: list[tuple[str, list[str]]] = field(default_factory=list)
    unused_macros: list[tuple[str, str]] = field(default_factory=list)
    orphan_only_macros: list[tuple[str, str]] = field(default_factory=list)
    dangling_ids: list[tuple[str, Hit]] = field(default_factory=list)
    hx_target_none: list[Hit] = field(default_factory=list)
    unmatched_urls: list[tuple[str, Hit]] = field(default_factory=list)
    method_mismatch: list[tuple[Route, Hit]] = field(default_factory=list)
    unreferenced_routes: list[tuple[str, Route]] = field(default_factory=list)
    unresolved: int = 0

    @property
    def total(self) -> int:
        return sum(
            len(v)
            for k, v in vars(self).items()
            if k != "unresolved" and isinstance(v, list)
        )


def analyse(
    hits: list[Hit],
    routes: list[Route],
    referenced: dict[str, set[str]],
    candidates: dict[str, set[str]],
) -> Report:
    report = Report()
    sources = {
        str(p.relative_to(TEMPLATES)): p.read_text()
        for p in sorted(TEMPLATES.rglob("*.jinja2"))
    }

    report.orphan_templates = [n for n in sources if not referenced[n]]
    orphans = set(report.orphan_templates)
    report.broken_template_refs = [
        (name, sorted(owners))
        for name, owners in sorted(referenced.items())
        if not (TEMPLATES / name).exists()
    ]

    # --- macros ------------------------------------------------------------
    defined: dict[str, str] = {}
    for owner, text in sources.items():
        for match in JINJA_MACRO.finditer(text):
            defined.setdefault(match.group(1), owner)
    for name, owner in sorted(defined.items()):
        callers = set()
        for holder, text in sources.items():
            for match in re.finditer(rf"\b{name}\s*\(", text):
                if re.search(
                    r"macro\s+$", text[max(0, match.start() - 16) : match.start()]
                ):
                    continue
                callers.add(holder)
        if not callers:
            report.unused_macros.append((name, owner))
        elif callers <= orphans:
            report.orphan_only_macros.append((name, owner))

    # --- DOM ids -----------------------------------------------------------
    # Checked against the union of every id in the app, not per-page: HTMX
    # swaps a partial into a live page, so a partial may legitimately point at
    # an id that only exists in the page hosting it.
    ids: set[str] = set()
    selectors: list[Hit] = []
    urls: list[Hit] = []
    for hit in hits:
        if hit.rule == "html-id":
            expanded = expand(hit.value, candidates)
            if not expanded or any(DYNAMIC in v for v in expanded):
                report.unresolved += 1
            ids.update(v for v in expanded if DYNAMIC not in v)
        elif hit.rule == "js-dom-id":
            ids.update(re.findall(r"#([A-Za-z0-9_-]+)", hit.value))
        elif hit.rule == "js-dom-id-assign":
            ids.add(hit.value)
        elif hit.rule == "html-htmx-selector":
            selectors.append(hit)
        elif hit.rule in ("html-htmx-url", "html-link", "js-url"):
            urls.append(replace(hit, value=collapse_markers(hit.value)))
        elif hit.rule == "html-hx-target-none":
            report.hx_target_none.append(hit)

    for hit in selectors:
        expanded = expand(hit.value, candidates)
        if not expanded or any(DYNAMIC in v for v in expanded):
            report.unresolved += 1
            continue
        for value in expanded:
            for name in re.findall(r"#([A-Za-z0-9_-]+)", value):
                if name not in ids:
                    report.dangling_ids.append((name, hit))

    # --- URLs vs routes ----------------------------------------------------
    url_hits = [
        h for h in urls if h.value.startswith("/") and not h.value.startswith("/static")
    ]
    for hit in url_hits:
        if DYNAMIC in hit.value:
            report.unresolved += 1
        matched = [r for r in routes if route_matches(r.path, hit.value)]
        if not matched:
            report.unmatched_urls.append((hit.value, hit))
            continue
        method = METHOD_OF.get(hit.attr)
        if method and not any(method in r.methods for r in matched):
            report.method_mismatch.append((matched[0], hit))

    test_text = "\n".join(p.read_text() for p in TESTS.rglob("*.py"))
    test_urls = [
        url.replace("{", DYNAMIC).replace("}", DYNAMIC)
        for url in re.findall(r"""["'](/[A-Za-z0-9_/{}\-]*)["']""", test_text)
    ]

    for route in routes:
        if route.path in ENTRY_POINTS:
            continue
        if any(route_matches(route.path, h.value) for h in url_hits):
            continue
        where = (
            "test-only"
            if any(route_matches(route.path, u) for u in test_urls)
            else "nowhere"
        )
        report.unreferenced_routes.append((where, route))

    return report


def render(report: Report) -> str:
    out: list[str] = []

    def section(title: str, lines: list[str]) -> None:
        if not lines:
            return
        out.append(f"\n{title} ({len(lines)})")
        out.append("-" * len(title))
        out.extend(lines)

    section(
        "Orphan templates -- referenced by nothing",
        [f"  {name}" for name in report.orphan_templates],
    )
    section(
        "Broken template references",
        [
            f"  {name}  <- {', '.join(owners)}"
            for name, owners in report.broken_template_refs
        ],
    )
    section(
        "Unused macros",
        [f"  {name}()  defined in {owner}" for name, owner in report.unused_macros],
    )
    section(
        "Macros only used by orphan templates",
        [
            f"  {name}()  defined in {owner}"
            for name, owner in report.orphan_only_macros
        ],
    )
    section(
        'hx-target="none" -- aborts the request',
        [f"  {hit.where()}" for hit in report.hx_target_none],
    )
    section(
        "Dangling #id selectors -- no matching id= anywhere",
        [
            f"  #{name}  at {hit.where()} ({hit.attr})"
            for name, hit in report.dangling_ids
        ],
    )
    section(
        "URLs with no matching route",
        [f"  {url}  at {hit.where()}" for url, hit in report.unmatched_urls],
    )
    section(
        "Method mismatch",
        [
            f"  {route.path} takes {', '.join(sorted(route.methods))}"
            f" but {hit.attr} at {hit.where()} is {METHOD_OF.get(hit.attr)}"
            for route, hit in report.method_mismatch
        ],
    )
    section(
        "Routes never requested from templates or JS",
        [
            f"  {where:10} {','.join(sorted(route.methods)):12} {route.path:42}"
            f" {route.handler}  ({route.file})"
            for where, route in report.unreferenced_routes
        ],
    )

    out.append(
        f"\n{report.total} finding(s); {report.unresolved} value(s) left dynamic."
    )
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--strict", action="store_true", help="exit 1 when anything is reported"
    )
    args = parser.parse_args()

    sources = {
        str(p.relative_to(TEMPLATES)): p.read_text()
        for p in sorted(TEMPLATES.rglob("*.jinja2"))
    }
    literals = local_literals(sources)
    candidates = all_candidates(literals)
    edges = include_edges(sources)

    # A template is a render root if it is a page, or if a route renders it
    # directly (`get_template(...)` / `TemplateResponse(...)`). Partials
    # returned by HTMX endpoints never appear in a page's include closure, so
    # without this they would never be scanned at all.
    py_text = "\n".join(p.read_text() for p in (ROOT / "src").rglob("*.py"))
    referenced: dict[str, set[str]] = defaultdict(set)
    for name in PY_TEMPLATE.findall(py_text):
        referenced[name].add("python")
    for owner, text in sources.items():
        for name in JINJA_REF.findall(text):
            referenced[name].add(owner)

    roots = sorted(
        name
        for name in sources
        if name.startswith("pages/") or "python" in referenced[name]
    )

    with tempfile.TemporaryDirectory(prefix="pipances-deadcode-") as tmp:
        index = build_mirror(Path(tmp), sources, literals, candidates, edges, roots)
        hits = scan(Path(tmp), index)

    report = analyse(hits, collect_routes(), referenced, candidates)

    if args.json:
        print(json.dumps(report, default=str, indent=2))
    else:
        print(render(report))
    return 1 if args.strict and report.total else 0


if __name__ == "__main__":
    raise SystemExit(main())
