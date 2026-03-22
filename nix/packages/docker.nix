{ pkgs, inputs, ... }:
let
  app = import ./financial-pipeline.nix { inherit pkgs inputs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "financial-pipeline";
  tag = "latest";

  contents = [
    app
    pkgs.coreutils
  ];

  config = {
    Cmd = [ "financial-pipeline" ];
    ExposedPorts = {
      "8097/tcp" = { };
    };
    Env = [
      "PIPANCES_DB_PATH=/data/financial_pipeline.db"
    ];
    Volumes = {
      "/data" = { };
    };
  };
}
