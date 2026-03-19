{
  description = "Financial pipeline dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    daisyui-css = {
      url = "https://cdn.jsdelivr.net/npm/daisyui@5/daisyui.css";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, daisyui-css }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in {
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            uv
            tailwindcss_4
            just
          ];
          env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
          ];
          shellHook = ''
            ln -sf ${daisyui-css} daisyui.css
          '';
        };
      });
    };
}
