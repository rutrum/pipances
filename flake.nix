{
  inputs = {
    blueprint.url = "github:numtide/blueprint";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    daisyui-css = {
      url = "https://cdn.jsdelivr.net/npm/daisyui@5/daisyui.css";
      flake = false;
    };
    htmx-js = {
      url = "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js";
      flake = false;
    };
    htmx-response-targets-js = {
      url = "https://unpkg.com/htmx-ext-response-targets@2.0.2/response-targets.js";
      flake = false;
    };
    lucide-js = {
      url = "https://unpkg.com/lucide@0.577.0/dist/umd/lucide.min.js";
      flake = false;
    };
    vega-js = {
      url = "https://cdn.jsdelivr.net/npm/vega@5.33.1/build/vega.min.js";
      flake = false;
    };
    vega-lite-js = {
      url = "https://cdn.jsdelivr.net/npm/vega-lite@5.23.0/build/vega-lite.min.js";
      flake = false;
    };
    vega-embed-js = {
      url = "https://cdn.jsdelivr.net/npm/vega-embed@6.29.0/build/vega-embed.min.js";
      flake = false;
    };
  };

  outputs = inputs: inputs.blueprint {
    inherit inputs;
    prefix = "nix/";
  };
}
