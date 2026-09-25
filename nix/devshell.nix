{
  pkgs,
  inputs,
  perSystem,
  system,
  ...
}:
let
  # The vendored asset list lives in nix/lib/assets.nix so this shell and the
  # production package can never disagree about what needs to exist on disk.
  assets = import ./lib/assets.nix { inherit pkgs inputs; };
in
pkgs.mkShell {
  packages = with pkgs; [
    uv
    tailwindcss_4
    just
    nodejs
    ast-grep
    prek
    typos
    nixfmt
    perSystem.self.agent-browser
    perSystem.self.skills
    sqlite
  ];

  env = {
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
    ];
    AGENT_BROWSER_EXECUTABLE_PATH = "${pkgs.chromium}/bin/chromium";
  };

  shellHook = ''
    ${assets.installBuildInputs {
      prefix = ".";
      mode = "symlink";
    }}
    ${assets.installServed {
      prefix = "static";
      mode = "symlink";
    }}
  '';
}
