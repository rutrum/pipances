{ pkgs, inputs, ... }:
let
  inherit (inputs) pyproject-nix uv2nix pyproject-build-systems;

  # Parse uv.lock at evaluation time
  workspace = uv2nix.lib.workspace.loadWorkspace {
    workspaceRoot = ../../.;
  };

  # Create overlay from lockfile (prefer wheels for fewer overrides)
  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };

  python = pkgs.python313;

  # Build the Python package set with all deps
  pythonSet =
    (pkgs.callPackage pyproject-nix.build.packages {
      inherit python;
    }).overrideScope
      (
        pkgs.lib.composeManyExtensions [
          pyproject-build-systems.overlays.default
          overlay
        ]
      );

  # Build the virtualenv with all runtime deps
  venv = pythonSet.mkVirtualEnv "pipances-env" workspace.deps.default;

  # Build static assets (JS from flake inputs + CSS from tailwind)
  staticAssets = pkgs.stdenvNoCC.mkDerivation {
    pname = "pipances-static";
    version = "0.1.0";
    src = ../../.;

    nativeBuildInputs = [ pkgs.tailwindcss_4 ];

    buildPhase = ''
      # Build CSS
      ln -sf ${inputs.daisyui-css} daisyui.css
      tailwindcss -i input.css -o static/css/style.css --minify
    '';

    installPhase = ''
      mkdir -p $out/static/js/external $out/static/css/external $out/static/js/pages

      # Copy built CSS
      cp static/css/style.css $out/static/css/

      # Copy first-party CSS (tracked in git)
      cp static/css/tabulator-daisy.css $out/static/css/

      # Copy vendor JS from flake inputs
      cp ${inputs.htmx-js} $out/static/js/external/htmx.min.js
      cp ${inputs.htmx-response-targets-js} $out/static/js/external/response-targets.js
      cp ${inputs.lucide-js} $out/static/js/external/lucide.min.js
      cp ${inputs.vega-js} $out/static/js/external/vega.min.js
      cp ${inputs.vega-lite-js} $out/static/js/external/vega-lite.min.js
      cp ${inputs.vega-embed-js} $out/static/js/external/vega-embed.min.js
      cp ${inputs.alpine-js} $out/static/js/external/alpine.min.js
      cp ${inputs.tom-select-js} $out/static/js/external/tom-select.complete.min.js
      cp ${inputs.tabulator-js} $out/static/js/external/tabulator.min.js

      # Copy vendor CSS from flake inputs
      cp ${inputs.tom-select-css} $out/static/css/external/tom-select.min.css
      cp ${inputs.tabulator-css} $out/static/css/external/tabulator.min.css

      # Copy first-party page scripts (tracked in git)
      cp -r static/js/pages/. $out/static/js/pages/
    '';
  };

  # Copy importers directory
  importers = pkgs.stdenvNoCC.mkDerivation {
    pname = "pipances-importers";
    version = "0.1.0";
    src = ../../importers;

    installPhase = ''
      mkdir -p $out
      cp -r $src/*.py $out/ 2>/dev/null || true
    '';
  };

in
pkgs.writeShellApplication {
  name = "pipances";
  runtimeInputs = [ venv ];
  text = ''
    export PIPANCES_STATIC_DIR="${staticAssets}/static"
    export PIPANCES_DB_PATH="''${PIPANCES_DB_PATH:-./pipances.db}"
    exec uvicorn pipances.main:app \
      --host "''${PIPANCES_HOST:-0.0.0.0}" \
      --port "''${PIPANCES_PORT:-8098}" \
      "$@"
  '';
}
