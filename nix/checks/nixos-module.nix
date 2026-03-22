{ pkgs, inputs, flake, system, ... }:
let
  # Evaluate the module with a minimal NixOS config
  eval = inputs.nixpkgs.lib.nixosSystem {
    inherit system;
    modules = [
      flake.nixosModules.pipances
      {
        # Minimal config to make NixOS evaluation happy
        boot.loader.grub.device = "nodev";
        fileSystems."/" = {
          device = "none";
          fsType = "tmpfs";
        };

        services.pipances = {
          enable = true;
          package = flake.packages.${system}.financial-pipeline;
        };
      }
    ];
  };
in
pkgs.runCommand "nixos-module-check" { } ''
  # Force evaluation of the system config
  echo "Evaluating NixOS module..."
  cat ${eval.config.system.build.etc}/etc/systemd/system/pipances.service > /dev/null
  echo "NixOS module evaluation succeeded"
  touch $out
''
