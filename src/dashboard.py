"""Build the self-contained browser dashboard from current analysis outputs."""

import json

import pandas as pd

from src.config import load_config, project_path


def _records(frame, columns):
    """Convert selected columns to JSON-safe Python records."""
    return json.loads(frame[columns].to_json(orient="records", double_precision=2))


def generate_dashboard(
    transactions,
    customer_rfm,
    segment_summary,
    category_summary,
    analysis_date,
):
    """Create an offline dashboard HTML file from the current analysis tables."""
    transactions = transactions.copy()
    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    )
    invoice_count = int(transactions["invoice_id"].nunique())
    revenue = float(transactions["line_revenue"].sum())
    monthly = (
        transactions.assign(
            month=transactions["transaction_date"].dt.to_period("M").astype(str)
        )
        .groupby("month", as_index=False)["line_revenue"]
        .sum()
        .rename(columns={"line_revenue": "revenue"})
    )
    config = load_config()
    risk_rule = next(
        (
            rule
            for rule in config["analysis"]["segments"]
            if rule.get("role") == "at_risk"
        ),
        None,
    )
    segments = segment_summary.copy()
    if risk_rule and not segments.empty:
        segments["role"] = segments["segment"].map(
            lambda label: "at_risk" if label == risk_rule["name"] else ""
        )
    else:
        segments["role"] = ""

    payload = {
        "currency": config["dataset"]["currency"],
        "period": {
            "start": transactions["transaction_date"].min().strftime("%Y-%m-%d"),
            "end": transactions["transaction_date"].max().strftime("%Y-%m-%d"),
            "analysis_date": pd.Timestamp(analysis_date).strftime("%Y-%m-%d"),
        },
        "summary": {
            "revenue": round(revenue, 2),
            "customers": int(transactions["customer_id"].nunique()),
            "invoices": invoice_count,
            "average_invoice_value": round(revenue / invoice_count, 2)
            if invoice_count
            else 0,
        },
        "monthly": _records(monthly, ["month", "revenue"]),
        "segments": _records(
            segments,
            [
                "segment",
                "customer_count",
                "total_revenue",
                "revenue_share_pct",
                "average_recency_days",
                "average_frequency",
                "average_monetary_value",
                "role",
            ],
        ),
        "categories": _records(
            category_summary,
            [
                "category",
                "revenue",
                "customer_count",
                "revenue_share_pct",
                "revenue_opportunity_score",
                "customer_reach_score",
                "performance_gap_score",
                "priority_score",
                "priority_rank",
                "equal_weight_rank",
            ],
        ),
        "customers": _records(
            customer_rfm.sort_values("monetary_value", ascending=False),
            [
                "customer_id",
                "segment",
                "recency_days",
                "frequency",
                "monetary_value",
                "rfm_code",
            ],
        ),
    }

    encoded_data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    encoded_data = (
        encoded_data.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("</", "<\\/")
    )
    template = project_path("dashboard_template").read_text(encoding="utf-8")
    dashboard_html = template.replace("__DASHBOARD_DATA__", encoded_data)
    output_path = project_path("dashboard_html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dashboard_html, encoding="utf-8")
    return output_path
