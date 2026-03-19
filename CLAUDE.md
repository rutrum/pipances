# Financial Analysis App

## Goals

I need a self hosted finances app that can help me track finances and visualize my expenses.

- load transactions dumps as csvs
- parse those csvs using defined polars expressions
- redundancy checking: transactions that are the same are discarded as already prcessed
- transactions are aligned to a fixed number of "sources" that I own: bank accounts, liabilities, credit cards
- web interface that allows me to 
  - upload transaction csvs into an "inbox" for review
  - review the inbox transactions in a table/grid
  - mark transactions as "human approved" where they are no longer in inbox
  - view all transactions
  - see a variety of statistics and graphs based on my transactions
- simple web login (single user, views all data)

## Non Goals

Some features I don't want for an initial release, despite them being good ideas.

- downloading/fetching transactions from banking institutions
- defining custom transaction schemas in the UI
- machine learning for auto filling in descriptions
- semantic search
- defining source accounts in the web UI

@AGENTS.md
