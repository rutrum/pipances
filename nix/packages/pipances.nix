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
      mkdir -p $out/static/js $out/static/css

      # Copy built CSS
      cp static/css/style.css $out/static/css/

      # Copy JS from flake inputs
      cp ${inputs.htmx-js} $out/static/js/htmx.min.js
      cp ${inputs.htmx-response-targets-js} $out/static/js/response-targets.js
      cp ${inputs.lucide-js} $out/static/js/lucide.min.js
      cp ${inputs.vega-js} $out/static/js/vega.min.js
      cp ${inputs.vega-lite-js} $out/static/js/vega-lite.min.js
      cp ${inputs.vega-embed-js} $out/static/js/vega-embed.min.js
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
