"""Run the complete cleaning, analysis, chart, and report workflow."""

import json

import pandas as pd

from src.config import ensure_project_directories, load_config, project_path
from src.customer_analysis import build_customer_analysis
from src.data_cleaning import clean_transactions
from src.product_analysis import build_category_analysis
from src.reporting import write_findings_report
from src.visualization import create_charts


def main():
    ensure_project_directories()
    raw_path = project_path("raw_transactions")
    if not raw_path.exists():
        raise FileNotFoundError(
            "Synthetic input data is missing. First run: python generate_data.py"
        )

    raw_transactions = pd.read_csv(raw_path)
    transactions, quality_summary = clean_transactions(raw_transactions)
    customer_rfm, segment_summary, analysis_date = build_customer_analysis(
        transactions
    )
    category_summary, priority_summary = build_category_analysis(transactions)

    transactions.to_csv(project_path("clean_transactions"), index=False)
    customer_rfm.to_csv(project_path("customer_rfm"), index=False)
    segment_summary.to_csv(project_path("segment_summary"), index=False)
    category_summary.to_csv(project_path("category_performance"), index=False)
    priority_summary.to_csv(project_path("category_priority"), index=False)
    project_path("data_quality_summary").write_text(
        json.dumps(quality_summary, indent=2), encoding="utf-8"
    )

    create_charts(transactions, segment_summary, category_summary)
    report_path = write_findings_report(
        transactions,
        customer_rfm,
        segment_summary,
        category_summary,
        priority_summary,
        quality_summary,
        analysis_date.date().isoformat(),
    )

    config = load_config()
    print("Analysis complete.")
    print(f"Clean rows: {len(transactions):,}")
    print(f"Customers: {customer_rfm['customer_id'].nunique():,}")
    print(
        f"Revenue: {config['dataset']['currency']} "
        f"{transactions['line_revenue'].sum():,.2f}"
    )
    print(f"Findings report saved to: {report_path}")


if __name__ == "__main__":
    main()
