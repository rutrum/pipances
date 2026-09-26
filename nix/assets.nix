{ pkgs, inputs }:
let
  # Vendor JS without dangling sourceMappingURL comments (the .map files are
  # not bundled, so the comments only produce 404 noise in browser devtools).
  stripSourcemap =
    file:
    pkgs.runCommand (builtins.baseNameOf file) { } ''
      cp ${file} $out
      sed -i '/sourceMappingURL/d' $out
    '';

  inherit (inputs)
    alpine-js
    daisyui-css
    htmx-js
    htmx-response-targets-js
    lucide-js
    tabulator-css
    tabulator-js
    tom-select-css
    tom-select-js
    vega-embed-js
    vega-js
    vega-lite-js
    ;

  # Files the app serves, keyed by path relative to `static/` — i.e. exactly the
  # suffix following `/static/` in the templates' hrefs/srcs.
  served = {
    "css/external/tabulator.min.css" = tabulator-css;
    "css/external/tom-select.min.css" = tom-select-css;

    "js/external/alpine.min.js" = alpine-js;
    "js/external/htmx.min.js" = htmx-js;
    "js/external/lucide.min.js" = stripSourcemap lucide-js;
    "js/external/response-targets.js" = htmx-response-targets-js;
    "js/external/tabulator.min.js" = stripSourcemap tabulator-js;
    "js/external/tom-select.complete.min.js" = stripSourcemap tom-select-js;
    "js/external/vega-embed.min.js" = stripSourcemap vega-embed-js;
    "js/external/vega-lite.min.js" = stripSourcemap vega-lite-js;
    "js/external/vega.min.js" = stripSourcemap vega-js;
  };

  # Files tooling reads from the repository root rather than the web server
  # (`input.css` does `@import "./nix/vendor/daisyui.css"`), keyed the same way.
  buildInputs = {
    "nix/vendor/daisyui.css" = daisyui-css;
  };

  # Shell snippet materialising `group` under `prefix`, creating parents as
  # needed. `mode` is "symlink" for trees we edit in place (devshell, the
  # package's build tree) and "copy" for store outputs.
  install =
    group:
    {
      prefix,
      mode ? "copy",
    }:
    let
      paths = builtins.attrNames group;
      dirs = builtins.filter (d: d != ".") (map builtins.dirOf paths);
    in
    pkgs.lib.concatStringsSep "\n" (
      map (d: "mkdir -p ${prefix}/${d}") (pkgs.lib.unique dirs)
      ++ map (p: "${if mode == "copy" then "cp -L" else "ln -sfn"} ${group.${p}} ${prefix}/${p}") paths
    );
in
{
  inherit served buildInputs;

  installServed = install served;
  installBuildInputs = install buildInputs;
}
