{
  inputs = {
    blueprint.url = "github:numtide/blueprint";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    daisyui-css = {
      url = "https://cdn.jsdelivr.net/npm/daisyui@5/daisyui.css";
      flake = false;
    };
  };

  outputs = inputs: inputs.blueprint {
    inherit inputs;
    prefix = "nix/";
  };
}
