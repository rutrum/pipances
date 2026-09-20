{
  pkgs,
  inputs,
  perSystem,
  system,
  ...
}:
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
    ln -sf ${inputs.daisyui-css} daisyui.css
    mkdir -p static/js/external static/css/external
    ln -sf ${inputs.htmx-js} static/js/external/htmx.min.js
    ln -sf ${inputs.htmx-response-targets-js} static/js/external/response-targets.js
    ln -sf ${inputs.lucide-js} static/js/external/lucide.min.js
    ln -sf ${inputs.vega-js} static/js/external/vega.min.js
    ln -sf ${inputs.vega-lite-js} static/js/external/vega-lite.min.js
    ln -sf ${inputs.vega-embed-js} static/js/external/vega-embed.min.js
    ln -sf ${inputs.alpine-js} static/js/external/alpine.min.js
    ln -sf ${inputs.tom-select-js} static/js/external/tom-select.complete.min.js
    ln -sf ${inputs.tom-select-css} static/css/external/tom-select.min.css
    ln -sf ${inputs.tabulator-js} static/js/external/tabulator.min.js
    ln -sf ${inputs.tabulator-css} static/css/external/tabulator.min.css
  '';
}
