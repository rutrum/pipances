{ pkgs, ... }:
let
  version = "1.4.5";
in
pkgs.stdenv.mkDerivation {
  pname = "skills";
  inherit version;

  src = pkgs.fetchurl {
    url = "https://registry.npmjs.org/skills/-/skills-${version}.tgz";
    hash = "sha512-fu73BeQ7dXDXx5/xViL7SOlSLamJAMlSLcyjoVTUGHCoQX5ekWrRVp0Go8OJqgzakUCIKqz8UijkDLBG9c/qOg==";
  };

  nativeBuildInputs = [ pkgs.makeWrapper ];

  unpackPhase = ''
    tar xzf $src
  '';

  sourceRoot = "package";

  installPhase = ''
    mkdir -p $out/lib/skills $out/bin
    cp -r . $out/lib/skills/
    makeWrapper ${pkgs.nodejs}/bin/node $out/bin/skills \
      --add-flags "$out/lib/skills/bin/cli.mjs"
    ln -s $out/bin/skills $out/bin/add-skill
  '';
}
