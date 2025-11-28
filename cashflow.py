import argparse
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DATA_FILE = Path("cashflow_data.json")


@dataclass
class Transaction:
    description: str
    amount: float
    type: str  # inflow or outflow
    recurrence: str  # one-time or recurring
    category: str
    month: Optional[str] = None
    start_month: Optional[str] = None
    end_month: Optional[str] = None
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.type not in {"inflow", "outflow"}:
            raise ValueError("type must be 'inflow' or 'outflow'")
        if self.recurrence not in {"one-time", "recurring"}:
            raise ValueError("recurrence must be 'one-time' or 'recurring'")
        if self.recurrence == "one-time" and not self.month:
            raise ValueError("one-time transactions require a month (YYYY-MM)")
        if self.recurrence == "recurring" and not self.start_month:
            raise ValueError("recurring transactions require start_month (YYYY-MM)")


def parse_month(value: str) -> str:
    datetime.strptime(value, "%Y-%m")
    return value


def load_data() -> Dict[str, List[Dict]]:
    if not DATA_FILE.exists():
        return {"transactions": []}
    return json.loads(DATA_FILE.read_text())


def save_data(data: Dict[str, List[Dict]]) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2))


def is_active_in_month(txn: Dict, target_month: str) -> bool:
    if txn["recurrence"] == "one-time":
        return txn["month"] == target_month

    start = txn["start_month"]
    end = txn.get("end_month")
    if start and start > target_month:
        return False
    if end and end < target_month:
        return False
    return True


def calculate_summary(data: Dict[str, List[Dict]], target_month: str, opening_balance: float) -> Dict:
    active_txns = [txn for txn in data.get("transactions", []) if is_active_in_month(txn, target_month)]
    inflows = sum(txn["amount"] for txn in active_txns if txn["type"] == "inflow")
    outflows = sum(txn["amount"] for txn in active_txns if txn["type"] == "outflow")
    net = inflows - outflows
    closing_balance = opening_balance + net
    return {
        "month": target_month,
        "opening_balance": opening_balance,
        "inflows": inflows,
        "outflows": outflows,
        "net": net,
        "closing_balance": closing_balance,
        "transactions": active_txns,
    }


def handle_add(args: argparse.Namespace) -> None:
    data = load_data()
    txn = Transaction(
        description=args.description,
        amount=args.amount,
        type=args.type,
        recurrence="recurring" if args.recurring else "one-time",
        category=args.category,
        month=args.month,
        start_month=args.start_month,
        end_month=args.end_month,
    )
    data.setdefault("transactions", []).append(asdict(txn))
    save_data(data)
    print(f"Added {txn.type} '{txn.description}' with id {txn.id}")


def handle_list(args: argparse.Namespace) -> None:
    data = load_data()
    txns = data.get("transactions", [])
    if args.month:
        txns = [txn for txn in txns if is_active_in_month(txn, args.month)]
    if not txns:
        print("No transactions found.")
        return

    for txn in txns:
        scope = txn["month"] if txn["recurrence"] == "one-time" else f"{txn['start_month']}+"
        end = txn.get("end_month")
        end_text = f" to {end}" if end else ""
        print(
            f"[{txn['id']}] {txn['description']} | {txn['type']} | ${txn['amount']:.2f} | {txn['recurrence']} ({scope}{end_text}) | {txn['category']}"
        )


def handle_summary(args: argparse.Namespace) -> None:
    data = load_data()
    summary = calculate_summary(data, args.month, args.opening_balance)
    print(f"Cash flow summary for {summary['month']}")
    print(f"Opening balance: ${summary['opening_balance']:.2f}")
    print(f"Total inflows:  ${summary['inflows']:.2f}")
    print(f"Total outflows: ${summary['outflows']:.2f}")
    print(f"Net income:      ${summary['net']:.2f}")
    print(f"Closing balance: ${summary['closing_balance']:.2f}")

    if summary["transactions"]:
        print("\nTransactions contributing to this month:")
        for txn in summary["transactions"]:
            source = txn["month"] if txn["recurrence"] == "one-time" else txn["start_month"]
            print(
                f"- {txn['description']} (${txn['amount']:.2f}, {txn['type']}, {txn['recurrence']}, from {source})"
            )


def handle_reset(_: argparse.Namespace) -> None:
    if DATA_FILE.exists():
        DATA_FILE.unlink()
        print("Cleared saved cash flow data.")
    else:
        print("No data file to clear.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal cash flow CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a cash flow item")
    add_parser.add_argument("description", help="Name of the inflow or outflow")
    add_parser.add_argument("amount", type=float, help="Dollar amount")
    add_parser.add_argument("type", choices=["inflow", "outflow"], help="Whether this is money in or out")
    add_parser.add_argument("category", help="Category label (e.g. rent, salary)")
    add_parser.add_argument("month", type=parse_month, nargs="?", help="Month for one-time items (YYYY-MM)")
    add_parser.add_argument("start_month", type=parse_month, nargs="?", help="Start month for recurring items (YYYY-MM)")
    add_parser.add_argument("end_month", type=parse_month, nargs="?", help="Optional end month for recurring items (YYYY-MM)")
    add_parser.add_argument("--recurring", action="store_true", help="Mark this as a recurring item")
    add_parser.set_defaults(func=handle_add)

    list_parser = subparsers.add_parser("list", help="List saved transactions")
    list_parser.add_argument("--month", type=parse_month, help="Filter transactions active in a month (YYYY-MM)")
    list_parser.set_defaults(func=handle_list)

    summary_parser = subparsers.add_parser("summary", help="Show the cash flow summary for a month")
    summary_parser.add_argument("month", type=parse_month, help="Month to summarize (YYYY-MM)")
    summary_parser.add_argument("--opening-balance", type=float, default=0.0, help="Starting balance for the month")
    summary_parser.set_defaults(func=handle_summary)

    reset_parser = subparsers.add_parser("reset", help="Clear saved data")
    reset_parser.set_defaults(func=handle_reset)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
