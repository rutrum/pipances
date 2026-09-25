{ pkgs, inputs, ... }:
let
  inherit (inputs) pyproject-nix uv2nix pyproject-build-systems;

  # Single source of truth for the app version: pyproject.toml.
  version = (builtins.fromTOML (builtins.readFile ../../pyproject.toml)).project.version;

  # Single source of truth for vendored JS/CSS plus the Tailwind build inputs.
  assets = import ../lib/assets.nix { inherit pkgs inputs; };

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
    inherit version;
    src = ../../.;

    nativeBuildInputs = [ pkgs.tailwindcss_4 ];

    buildPhase = ''
      # Build CSS. The daisyUI import is a build input, materialised exactly like
      # every other Nix-managed file rather than special-cased here.
      ${assets.installBuildInputs {
        prefix = ".";
        mode = "symlink";
      }}
      tailwindcss -i input.css -o static/css/style.css --minify
    '';

    installPhase = ''
      mkdir -p $out/static

      # First-party assets are copied wholesale rather than enumerated, so a new
      # table/page script ships without anyone remembering to update this file.
      # The vendor directories do not exist in the store source (they are
      # gitignored) and are materialised below.
      cp -r static/. $out/static/

      # Vendored JS/CSS from flake inputs, via the shared manifest.
      ${assets.installServed {
        prefix = "$out/static";
        mode = "copy";
      }}
    '';
  };

  # Copy importers directory
  importers = pkgs.stdenvNoCC.mkDerivation {
    pname = "pipances-importers";
    inherit version;
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
