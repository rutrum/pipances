{ pkgs, inputs, perSystem, ... }:
pkgs.mkShell {
  packages = with pkgs; [
    uv
    tailwindcss_4
    just
    perSystem.self.agent-browser
  ];
  env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
  ];
  env.AGENT_BROWSER_EXECUTABLE_PATH = "${pkgs.chromium}/bin/chromium";
  shellHook = ''
    ln -sf ${inputs.daisyui-css} daisyui.css
  '';
}
