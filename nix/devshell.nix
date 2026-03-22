{ pkgs, inputs, perSystem, ... }:
pkgs.mkShell {
  packages = with pkgs; [
    uv
    tailwindcss_4
    just
    perSystem.self.agent-browser
    perSystem.self.skills
    sqlite
  ];
  env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
  ];
  env.AGENT_BROWSER_EXECUTABLE_PATH = "${pkgs.chromium}/bin/chromium";
  shellHook = ''
    ln -sf ${inputs.daisyui-css} daisyui.css
    mkdir -p static/js
    ln -sf ${inputs.htmx-js} static/js/htmx.min.js
    ln -sf ${inputs.htmx-response-targets-js} static/js/response-targets.js
    ln -sf ${inputs.lucide-js} static/js/lucide.min.js
    ln -sf ${inputs.vega-js} static/js/vega.min.js
    ln -sf ${inputs.vega-lite-js} static/js/vega-lite.min.js
    ln -sf ${inputs.vega-embed-js} static/js/vega-embed.min.js
  '';
}
