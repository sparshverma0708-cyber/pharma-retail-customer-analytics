"""Write a concise, evidence-based findings and recommendation report."""

from src.config import load_config, project_path


def write_findings_report(
    transactions,
    customer_rfm,
    segment_summary,
    category_summary,
    priority_summary,
    quality_summary,
    analysis_date,
):
    config = load_config()
    currency = config["dataset"]["currency"]
    start_date = transactions["transaction_date"].min()
    end_date = transactions["transaction_date"].max()
    total_revenue = transactions["line_revenue"].sum()
    top_category = category_summary.sort_values("revenue", ascending=False).iloc[0]
    priority_category = priority_summary.iloc[0]

    at_risk_rule = next(
        (
            rule
            for rule in config["analysis"]["segments"]
            if rule.get("role") == "at_risk"
        ),
        None,
    )
    at_risk_name = at_risk_rule["name"] if at_risk_rule else None
    if at_risk_name:
        at_risk = segment_summary.loc[
            segment_summary["segment"].eq(at_risk_name)
        ]
    else:
        at_risk = segment_summary.iloc[0:0]
    at_risk_count = int(at_risk["customer_count"].sum()) if not at_risk.empty else 0
    at_risk_revenue = float(at_risk["total_revenue"].sum()) if not at_risk.empty else 0.0

    segment_lines = [
        f"| {row.segment} | {int(row.customer_count):,} | "
        f"{currency} {row.total_revenue:,.2f} | {row.revenue_share_pct:.1f}% |"
        for row in segment_summary.sort_values(
            "total_revenue", ascending=False
        ).itertuples()
    ]
    category_lines = [
        f"| {row.category} | {currency} {row.revenue:,.2f} | "
        f"{int(row.customer_count):,} | {row.priority_score:.1f} | "
        f"{int(row.priority_rank)} |"
        for row in category_summary.sort_values(
            "priority_rank"
        ).itertuples()
    ]

    recommendation_lines = [
        f"1. **Review {priority_category.category} first.** It ranks "
        f"{int(priority_category.priority_rank)} on the configured review score "
        f"({priority_category.priority_score:.1f}/100). Inspect customer reach "
        "and the revenue-per-customer gap, then test a small, measurable "
        "merchandising or availability change.",
        f"2. **Protect the leading category.** {top_category.category} contributes "
        f"{top_category.revenue_share_pct:.1f}% of observed revenue. Review stock "
        "availability and monitor category revenue and in-stock rate.",
    ]
    if at_risk_count:
        recommendation_lines.append(
            f"3. **Test a customer win-back.** The rule-based {at_risk_name} "
            f"segment has {at_risk_count:,} customers and "
            f"{currency} {at_risk_revenue:,.2f} in historical period revenue. "
            "Use a holdout group and compare repeat purchase rate and incremental "
            "revenue before expanding any offer."
        )
    recommendation_lines.append(
        "These are hypotheses for business testing, not guaranteed outcomes. "
        "Transaction history alone does not explain customer needs or support "
        "medical advice."
    )

    report = f"""# Analysis findings

## Dataset and scope

- Data type: synthetic pharmacy retail transactions; no real customer or health information.
- Transaction period: {start_date} to {end_date}.
- RFM analysis date: {analysis_date} (the day after the final transaction date).
- Clean line items: {len(transactions):,}.
- Customers: {customer_rfm['customer_id'].nunique():,}.
- Revenue after discounts: {currency} {total_revenue:,.2f}.

## Data preparation

| Measure | Rows |
|---|---:|
| Input line items | {quality_summary['input_rows']:,} |
| Missing or unparsed rows removed | {quality_summary['rows_with_missing_or_unparsed_values_removed']:,} |
| Exact duplicate rows removed | {quality_summary['duplicate_rows_removed']:,} |
| Invalid sales rows removed | {quality_summary['rows_with_invalid_sales_values_removed']:,} |
| Revenue values recalculated | {quality_summary['revenue_values_recalculated']:,} |
| Clean line items | {quality_summary['clean_rows']:,} |

## Customer segments

| Segment | Customers | Revenue | Revenue share |
|---|---:|---:|---:|
{chr(10).join(segment_lines)}

## Category review priority

The score is a relative review aid built from revenue opportunity, customer reach, and a below-average revenue-per-customer gap. Component weights are editable in project_config.json. It does not predict growth or profit.

| Category | Revenue | Customers | Score / 100 | Rank |
|---|---:|---:|---:|---:|
{chr(10).join(category_lines)}

The highest revenue category is **{top_category.category}**. The first category to review under the configured score is **{priority_category.category}**. Compare the configured ranking with the equal-weight ranking in outputs/tables/category_priority.csv; a ranking change indicates weight sensitivity.

## Suggested actions to test

{chr(10).join(recommendation_lines)}

## Limitations

- All records are synthetic and illustrate a workflow only; they do not establish real pharmacy behavior.
- Revenue is not profit. Product cost, returns, stock availability, and operating costs are not included.
- RFM segments are descriptive rules for the selected period, not customer identities or predictions.
- Category comparisons can reflect the synthetic data-generation choices and the selected date range.
"""
    report_path = project_path("report")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report_path
