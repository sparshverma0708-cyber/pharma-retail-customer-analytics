"""Product category performance and an explainable review-priority score."""

import pandas as pd

from src.config import load_config


def build_category_analysis(transactions):
    """Summarize category performance and compare score rankings by weights."""
    invoice_category = transactions.groupby(
        ["category", "invoice_id"], as_index=False
    )["line_revenue"].sum()
    category_summary = transactions.groupby("category", as_index=False).agg(
        revenue=("line_revenue", "sum"),
        units_sold=("quantity", "sum"),
        customer_count=("customer_id", "nunique"),
        product_count=("product_id", "nunique"),
    )
    invoice_counts = invoice_category.groupby("category")["invoice_id"].nunique().rename(
        "invoice_count"
    )
    category_summary = category_summary.join(invoice_counts, on="category")
    total_revenue = category_summary["revenue"].sum()
    total_customers = transactions["customer_id"].nunique()
    category_summary["revenue_share_pct"] = (
        category_summary["revenue"] / total_revenue * 100
    )
    category_summary["customer_reach_pct"] = (
        category_summary["customer_count"] / total_customers * 100
    )
    category_summary["revenue_per_customer"] = (
        category_summary["revenue"] / category_summary["customer_count"]
    )
    category_summary["revenue_per_invoice"] = (
        category_summary["revenue"] / category_summary["invoice_count"]
    )
    category_summary = category_summary.sort_values(
        "revenue", ascending=False
    ).reset_index(drop=True)

    weights = load_config()["analysis"]["priority_weights"]
    if not abs(sum(weights.values()) - 1.0) < 1e-9:
        raise ValueError("Configured priority weights must sum to 1.0.")

    category_summary["revenue_opportunity_score"] = _scale_to_100(
        category_summary["revenue"]
    )
    category_summary["customer_reach_score"] = _scale_to_100(
        category_summary["customer_count"]
    )
    average_category_revenue_per_customer = (
        category_summary["revenue"].sum()
        / category_summary["customer_count"].sum()
    )
    below_average_gap = (
        average_category_revenue_per_customer
        - category_summary["revenue_per_customer"]
    ).clip(lower=0)
    category_summary["performance_gap_score"] = _scale_to_100(below_average_gap)
    category_summary["priority_score"] = (
        category_summary["revenue_opportunity_score"]
        * weights["revenue_opportunity"]
        + category_summary["customer_reach_score"]
        * weights["customer_reach"]
        + category_summary["performance_gap_score"]
        * weights["performance_gap"]
    )

    equal_weight_score = (
        category_summary["revenue_opportunity_score"]
        + category_summary["customer_reach_score"]
        + category_summary["performance_gap_score"]
    ) / 3
    category_summary["equal_weight_rank"] = equal_weight_score.rank(
        method="min", ascending=False
    ).astype(int)
    category_summary["priority_rank"] = category_summary["priority_score"].rank(
        method="min", ascending=False
    ).astype(int)

    numeric_columns = category_summary.select_dtypes(include="number").columns
    category_summary[numeric_columns] = category_summary[numeric_columns].round(2)
    priority_columns = [
        "category",
        "priority_rank",
        "priority_score",
        "revenue_opportunity_score",
        "customer_reach_score",
        "performance_gap_score",
        "equal_weight_rank",
    ]
    priority_summary = category_summary[priority_columns].sort_values(
        "priority_rank"
    ).reset_index(drop=True)
    return category_summary, priority_summary


def _scale_to_100(values):
    """Scale a measure against its maximum, retaining zero for all-zero values."""
    maximum = values.max()
    if maximum == 0:
        return pd.Series(0.0, index=values.index)
    return values / maximum * 100
