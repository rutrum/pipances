{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.pipances;
in
{
  options.services.pipances = {
    enable = lib.mkEnableOption "Pipances financial transaction pipeline";

    package = lib.mkOption {
      type = lib.types.package;
      description = "The Pipances package to use.";
    };

    host = lib.mkOption {
      type = lib.types.str;
      default = "0.0.0.0";
      description = "Address to bind the web server to.";
    };

    port = lib.mkOption {
      type = lib.types.port;
      default = 8097;
      description = "Port to listen on.";
    };

    dataDir = lib.mkOption {
      type = lib.types.str;
      default = "/var/lib/pipances";
      description = "Directory for the SQLite database.";
    };

    importersDir = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = "Path to custom importers directory. When null, uses the built-in importers from the package.";
    };

    openFirewall = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Whether to open the firewall port.";
    };

    user = lib.mkOption {
      type = lib.types.str;
      default = "pipances";
      description = "User account under which the service runs.";
    };

    group = lib.mkOption {
      type = lib.types.str;
      default = "pipances";
      description = "Group under which the service runs.";
    };
  };

  config = lib.mkIf cfg.enable {
    users.users.${cfg.user} = {
      isSystemUser = true;
      group = cfg.group;
      home = cfg.dataDir;
    };

    users.groups.${cfg.group} = { };

    systemd.services.pipances = {
      description = "Pipances financial transaction pipeline";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      environment = {
        PIPANCES_DB_PATH = "${cfg.dataDir}/pipances.db";
        PIPANCES_HOST = cfg.host;
        PIPANCES_PORT = toString cfg.port;
      } // lib.optionalAttrs (cfg.importersDir != null) {
        PIPANCES_IMPORTERS_DIR = toString cfg.importersDir;
      };

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/financial-pipeline";
        User = cfg.user;
        Group = cfg.group;
        StateDirectory = "pipances";
        WorkingDirectory = cfg.dataDir;
        Restart = "on-failure";

        # Hardening
        ProtectHome = true;
        NoNewPrivileges = true;
        ProtectSystem = "strict";
        PrivateTmp = true;
        ReadWritePaths = [ cfg.dataDir ];
      };
    };

    networking.firewall.allowedTCPPorts = lib.mkIf cfg.openFirewall [ cfg.port ];
  };
}
