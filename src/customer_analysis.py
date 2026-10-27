"""Customer metrics, RFM scoring, and rule-based customer groups."""

import pandas as pd

from src.config import load_config


def _score_quantiles(values, bucket_count, higher_is_better):
    """Convert a numeric column into 1..N quantile scores, handling ties safely."""
    usable_bucket_count = min(bucket_count, len(values))
    ranked_values = values.rank(method="first", ascending=True)
    quantile_codes = pd.qcut(
        ranked_values, q=usable_bucket_count, labels=False
    ).astype(int)
    if higher_is_better:
        return quantile_codes + 1
    return usable_bucket_count - quantile_codes


def _condition_matches(series, limits):
    matched = pd.Series(True, index=series.index)
    if "min" in limits:
        matched &= series.ge(limits["min"])
    if "max" in limits:
        matched &= series.le(limits["max"])
    return matched


def _rule_matches(customer_rows, rule):
    all_conditions = rule.get("all_conditions", {})
    any_conditions = rule.get("any_conditions", {})
    all_match = pd.Series(True, index=customer_rows.index)
    for column, limits in all_conditions.items():
        all_match &= _condition_matches(customer_rows[column], limits)
    if not any_conditions:
        return all_match
    any_match = pd.Series(False, index=customer_rows.index)
    for column, limits in any_conditions.items():
        any_match |= _condition_matches(customer_rows[column], limits)
    return all_match & any_match


def build_customer_analysis(transactions):
    """Build one customer row with RFM measures and a configured segment label."""
    config = load_config()
    settings = config["analysis"]
    transactions = transactions.copy()
    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    )
    invoice_totals = transactions.groupby(
        ["customer_id", "invoice_id"], as_index=False
    )["line_revenue"].sum()

    customer_summary = transactions.groupby("customer_id").agg(
        last_purchase_date=("transaction_date", "max"),
        monetary_value=("line_revenue", "sum"),
        units_purchased=("quantity", "sum"),
    )
    invoice_frequency = (
        invoice_totals.groupby("customer_id")["invoice_id"]
        .nunique()
        .rename("frequency")
    )
    customer_summary = customer_summary.join(invoice_frequency)
    analysis_date = transactions["transaction_date"].max() + pd.Timedelta(days=1)
    customer_summary["recency_days"] = (
        analysis_date - customer_summary["last_purchase_date"]
    ).dt.days

    bucket_count = settings["rfm_bucket_count"]
    customer_summary["recency_score"] = _score_quantiles(
        customer_summary["recency_days"], bucket_count, higher_is_better=False
    )
    customer_summary["frequency_score"] = _score_quantiles(
        customer_summary["frequency"], bucket_count, higher_is_better=True
    )
    customer_summary["monetary_score"] = _score_quantiles(
        customer_summary["monetary_value"], bucket_count, higher_is_better=True
    )
    customer_summary["rfm_score"] = customer_summary[
        ["recency_score", "frequency_score", "monetary_score"]
    ].sum(axis=1)
    customer_summary["rfm_code"] = customer_summary[
        ["recency_score", "frequency_score", "monetary_score"]
    ].astype(str).agg("".join, axis=1)

    customer_summary["segment"] = "Unassigned"
    for rule in settings["segments"]:
        matches = _rule_matches(customer_summary, rule)
        unassigned = customer_summary["segment"].eq("Unassigned")
        customer_summary.loc[matches & unassigned, "segment"] = rule["name"]
    if customer_summary["segment"].eq("Unassigned").any():
        raise ValueError("Every customer must match a configured segment rule.")

    customer_summary = customer_summary.reset_index()
    customer_summary["last_purchase_date"] = customer_summary[
        "last_purchase_date"
    ].dt.strftime("%Y-%m-%d")
    segment_summary = customer_summary.groupby("segment", as_index=False).agg(
        customer_count=("customer_id", "nunique"),
        total_revenue=("monetary_value", "sum"),
        average_recency_days=("recency_days", "mean"),
        average_frequency=("frequency", "mean"),
        average_monetary_value=("monetary_value", "mean"),
    )
    total_revenue = customer_summary["monetary_value"].sum()
    segment_summary["revenue_share_pct"] = (
        segment_summary["total_revenue"] / total_revenue * 100
    ).round(2)
    return customer_summary, segment_summary, analysis_date
