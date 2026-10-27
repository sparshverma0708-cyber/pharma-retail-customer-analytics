"""Validate and prepare transaction rows for analysis."""

import pandas as pd


REQUIRED_COLUMNS = [
    "customer_id",
    "invoice_id",
    "transaction_date",
    "product_id",
    "product_name",
    "category",
    "quantity",
    "unit_price",
    "discount_amount",
    "line_revenue",
    "currency",
]


def clean_transactions(raw_transactions):
    """Return cleaned rows plus counts that explain the cleaning decisions."""
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(raw_transactions.columns))
    if missing_columns:
        raise ValueError(f"Required columns are missing: {', '.join(missing_columns)}")

    transactions = raw_transactions[REQUIRED_COLUMNS].copy()
    starting_rows = len(transactions)
    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"], errors="coerce"
    )
    numeric_columns = ["quantity", "unit_price", "discount_amount", "line_revenue"]
    for column in numeric_columns:
        transactions[column] = pd.to_numeric(transactions[column], errors="coerce")

    missing_or_unparsed = transactions.isna().any(axis=1)
    transactions = transactions.loc[~missing_or_unparsed].copy()
    missing_or_unparsed_rows = int(missing_or_unparsed.sum())

    duplicate_rows = transactions.duplicated().sum()
    transactions = transactions.drop_duplicates().copy()

    valid_values = (
        transactions["quantity"].gt(0)
        & transactions["unit_price"].ge(0)
        & transactions["discount_amount"].ge(0)
        & transactions["discount_amount"].le(
            transactions["quantity"] * transactions["unit_price"]
        )
    )
    invalid_value_rows = int((~valid_values).sum())
    transactions = transactions.loc[valid_values].copy()

    expected_revenue = (
        transactions["quantity"] * transactions["unit_price"]
        - transactions["discount_amount"]
    ).round(2)
    revenue_mismatch_rows = int(
        (transactions["line_revenue"].round(2) != expected_revenue).sum()
    )
    transactions["line_revenue"] = expected_revenue
    transactions["transaction_date"] = transactions[
        "transaction_date"
    ].dt.strftime("%Y-%m-%d")
    transactions = transactions.sort_values(
        ["transaction_date", "invoice_id", "product_id"]
    ).reset_index(drop=True)

    quality_summary = {
        "input_rows": int(starting_rows),
        "rows_with_missing_or_unparsed_values_removed": missing_or_unparsed_rows,
        "duplicate_rows_removed": int(duplicate_rows),
        "rows_with_invalid_sales_values_removed": invalid_value_rows,
        "revenue_values_recalculated": revenue_mismatch_rows,
        "clean_rows": int(len(transactions)),
    }
    return transactions, quality_summary
