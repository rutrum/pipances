{ pkgs, inputs, ... }:
let
  app = import ./pipances.nix { inherit pkgs inputs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "pipances";
  tag = "latest";

  contents = [
    app
    pkgs.coreutils
  ];

  config = {
    Cmd = [ "pipances" ];
    ExposedPorts = {
      "8097/tcp" = { };
    };
    Env = [
      "PIPANCES_DB_PATH=/data/pipances.db"
      "PIPANCES_IMPORTERS_DIR=/data/importers"
    ];
    Volumes = {
      "/data" = { };
    };
  };
}
