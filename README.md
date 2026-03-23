# Pipances

Self-hosted finance tracker with ML-assisted human review.

## Philosophy

Most approaches to personal finance tracking fall into two extremes: fully automatic categorization that gets things wrong silently, or tedious manual entry for every transaction. Pipances combines both — automation handles the grunt work, but every transaction passes through a human review gate before becoming part of your financial record.

The core workflow:

```
CSV Import → Parse → Deduplicate → ML Predict → Human Review → Approved
```

You upload bank exports, the system parses them with institution-specific importers, deduplicates against existing records, and uses machine learning to predict categories and descriptions. Then you review the inbox, correct anything the model got wrong, and approve. Over time, the model learns from your corrections and gets better.

## Features

- **CSV import** with pluggable importers for different bank formats
- **ML-assisted categorization** — predictions for category, description, and external account based on your approved history
- **Inbox review workflow** — bulk edit, filter, and approve pending transactions
- **Explore page** — interactive charts, summary statistics, and filtered transaction browsing
- **Multiple account types** — checking, savings, credit cards, with account lifecycle (open/close)
- **Self-hosted** — SQLite-backed, runs as a single process, your data stays with you

## Installation

### Nix

Run directly from the flake:

```sh
nix run github:rutrum/pipances
```

Or add to a NixOS configuration:

```nix
{
  inputs.pipances.url = "github:rutrum/pipances";

  # In your NixOS config:
  services.pipances = {
    enable = true;
    package = inputs.pipances.packages.${system}.pipances;
    # dataDir = "/var/lib/pipances";  # default
    # port = 8097;                     # default
    # importersDir = ./my-importers;   # optional
  };
}
```

### Docker

The OCI image is built via Nix:

```sh
nix build .#docker
podman load < result
podman run -p 8097:8097 -v pipances-data:/data pipances:latest
```

### Python

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```sh
git clone https://github.com/rutrum/pipances
cd pipances
uv sync
uv run tailwindcss -i input.css -o static/css/style.css
uv run python -m pipances.main
```

## Configuration

Pipances is configured via environment variables:

| Variable | Default | Description |
|---|---|---|
| `PIPANCES_DB_PATH` | `./pipances.db` | Path to the SQLite database file |
| `PIPANCES_HOST` | `0.0.0.0` | Address to bind the web server |
| `PIPANCES_PORT` | `8097` | Port to listen on |
| `PIPANCES_IMPORTERS_DIR` | `./importers` | Directory containing importer modules |
| `PIPANCES_STATIC_DIR` | `./static` | Directory for static assets (CSS/JS) |

### Custom Importers

Importers are Python files that define how to parse a bank's CSV format. Place them in the importers directory. Each importer exports an `IMPORTER_NAME` string and a `parse(blob: bytes) -> polars.DataFrame` function that returns a DataFrame with `date`, `amount`, and `description` columns.

See `importers/example.py` for a reference implementation.
