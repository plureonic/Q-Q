# Personal Cash Flow CLI

A lightweight command-line tool to track inflows and outflows, whether they are recurring or one-time, and to calculate monthly cash-flow summaries with opening and closing balances.

## Features
- Add inflows or outflows with categories.
- Support recurring items with optional end months and one-time items tied to a specific month.
- List all saved transactions or only those active in a given month.
- Calculate monthly totals, net income, and closing balance from an opening balance.
- Reset stored data.

## Installation
The tool relies only on the Python standard library. No extra packages are needed.

## Usage
```
python cashflow.py add "Salary" 3000 inflow income 2024-01 --recurring
python cashflow.py add "Rent" 1200 outflow housing 2024-01 --recurring
python cashflow.py add "Vacation" 500 outflow fun 2024-02
python cashflow.py list --month 2024-02
python cashflow.py summary 2024-02 --opening-balance 200
python cashflow.py reset
```

Transactions are stored in `cashflow_data.json` in the current directory.
