# Financial Pipeline

Self-hosted finance tracker.

## Development

Requires [Nix](https://nixos.org/) with flakes enabled.

```sh
nix develop
just setup   # install deps + build CSS
just serve   # run dev server at :8000
```

Run `just --list` for all available recipes.
