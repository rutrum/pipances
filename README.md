# Pipances

Self-hosted finance tracker with ML-assisted human review.

## Philosophy

I previously used Firefly III, but had some gripes with it.  It took too long to add transactions.  Automated importing and rules-based automations are possible, but there _was no human review step_ which never gave me the confidence to use these features.  If something was automatically categorized, it would be very difficult for me to find what the result was, and correct errors manually.  So I was manually adding transactions, which was time consuming.  Adding transactions in Firefly presented a lot of fields I didn't care about, and it had no capabilities of bulk adding and limited capabilities for bulk editing.

So pipances is fundamentally centered around human approval.  Required human approval means I can leverage powerful automations but always be confident that the final result is accurate.  Inspired by "the data science pipeline" pipances imagines your financial transactions as flowing through the application.

1. Import: import csv dumps straight from your financial institution.  These are parsed with hand made parsers to match the bank's custom format into a normalized one.
2. Predict: a machine learning model built on all previously inserted transactions tries to fill in values for the transaction description, foreign account, and category.
3. Inbox: imported transactions end up in the inbox.  This is where the user can see all transactions and predicted fields, and then make edits or fill in blanks.  The user can stage individual transactions and "commit" then in bulk, as a human sign off of accurate labeling.
4. Explore: browse committed transactions to see trends and make predictions.

This vision is here in spirit, but the application is rough around the edges and needs a lot of work.

## Features

- **CSV import** with user-written python importers for different bank formats
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
    # dataDir = "/var/lib/pipances";   # default
    # port = 8098;                     # default
    # importersDir = ./my-importers;   # optional
  };
}
```

### Container (docker/podman)

The OCI image is built via Nix:

```sh
nix build .#docker
podman load < result
podman run -p 8098:8098 -v pipances-data:/data pipances:latest
```

### Build from Source

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```sh
git clone https://github.com/rutrum/pipances
cd pipances
just setup        # sync deps and build CSS
just serve        # run dev server on port 8098
```

## Configuration

Pipances is configured via environment variables:

| Variable | Default | Description |
|---|---|---|
| `PIPANCES_DB_PATH` | `./pipances.db` | Path to the SQLite database file |
| `PIPANCES_HOST` | `0.0.0.0` | Address to bind the web server |
| `PIPANCES_PORT` | `8098` | Port to listen on |
| `PIPANCES_IMPORTERS_DIR` | `./importers` | Directory containing importer modules |
| `PIPANCES_STATIC_DIR` | `./static` | Directory for static assets (CSS/JS) |

### Custom Importers

Importers are Python files that define how to parse a bank's CSV format. Place them in the importers directory. Each importer exports an `IMPORTER_NAME` string and a `parse(blob: bytes) -> polars.DataFrame` function that returns a DataFrame with `date`, `amount`, and `description` columns.

See `importers/example.py` for a reference implementation.
