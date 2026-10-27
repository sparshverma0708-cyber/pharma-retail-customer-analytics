# Pharma Retail Customer Segmentation & Revenue Optimization

An end-to-end, beginner-friendly analytics project using **synthetic pharmacy retail transactions**. It demonstrates data cleaning, customer RFM analysis, rule-based segmentation, category performance, a transparent review-priority score, and business recommendations.

> **Data notice:** The included transactions are synthetic and contain no real customer or health information. They demonstrate an analysis workflow; they cannot prove how real customers behave or whether a business action will increase revenue.

## Project question

How can a pharmacy retailer describe customer purchasing behavior, understand revenue contribution, and identify customer or product areas to investigate?

This project answers that question with descriptive analysis. It does not make medical recommendations, predict customer behavior, or calculate profit.

## Quick start

You need Python 3.10 or newer. From the project folder, open a terminal and run:

```bash
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- macOS or Linux: `source .venv/bin/activate`

Install packages and run the project:

```bash
python -m pip install -r requirements.txt
python run_project.py
```

The supplied synthetic transaction file is ready to analyze. To use the optional notebook, install Jupyter with python -m pip install jupyter, launch jupyter notebook from this folder, and open notebooks/01_analysis_walkthrough.ipynb. To recreate it from the product catalog and project settings, run:

```bash
python generate_data.py
python run_project.py
```

The run creates cleaned data, analysis tables, browser-friendly SVG charts, a quality summary, and a findings report. SVG charts need no plotting-library install. All input and output locations are set in `project_config.json`, using paths relative to this project folder. No machine-specific paths are required.

## Project structure

```text
pharma-retail-customer-analytics/
├── README.md
├── project_config.json
├── requirements.txt
├── .gitignore
├── generate_data.py
├── run_project.py
├── data/
│   ├── raw/
│   │   ├── product_catalog.csv
│   │   └── synthetic_transactions.csv
│   └── processed/                 # Created when the analysis runs
├── notebooks/
│   └── 01_analysis_walkthrough.ipynb
├── src/
│   ├── config.py
│   ├── data_generation.py
│   ├── data_cleaning.py
│   ├── customer_analysis.py
│   ├── product_analysis.py
│   ├── visualization.py
│   └── reporting.py
├── outputs/
│   ├── figures/                   # Charts created by the analysis
│   └── tables/                    # CSV summaries created by the analysis
└── reports/
    └── findings.md                # Generated findings and recommendations
```

## Dataset design and data dictionary

Each transaction row represents one product line on one invoice. The data generator uses anonymous customer and invoice IDs, a separate product catalog, a fixed date range, and a reproducible random seed. Product prices, categories, and sampling weights live in `data/raw/product_catalog.csv`; generation settings live in `project_config.json`.

| Column | Meaning | Example |
|---|---|---|
| `customer_id` | Anonymous customer identifier | `C00042` |
| `invoice_id` | Unique invoice identifier | `INV0000123` |
| `transaction_date` | Sale date in ISO format | `2025-03-14` |
| `product_id` | Product catalog key | `P005` |
| `product_name` | Generic synthetic product label | `Vitamin C Tablets` |
| `category` | Product category | `Vitamins` |
| `quantity` | Units on this invoice line | `2` |
| `unit_price` | Price per unit in the configured currency | `8.40` |
| `discount_amount` | Discount for the line, not per unit | `0.84` |
| `line_revenue` | Quantity × unit price − line discount | `15.96` |
| `currency` | Currency code for the transaction | `USD` |

The product catalog also has a sampling weight; the example gives products equal weights. The sample settings create 300 anonymous customers over one year. The exact row count is generated from configured purchase profiles and will be reproducible while the random seed and settings stay the same.

## Data pipeline

1. **Generate or load data:** Read the synthetic transaction CSV and product catalog.
2. **Clean and validate:** Parse dates and numbers, remove rows with missing or invalid sales values, remove exact duplicate rows, and recalculate revenue from quantity, price, and discount.
3. **Create customer features:** Aggregate line items to customer and invoice level.
4. **Calculate RFM:** Measure recency, frequency, and monetary value; score each measure into configurable quantile buckets.
5. **Assign customer groups:** Apply ordered, editable rules from the configuration file.
6. **Analyze products and categories:** Summarize revenue, units, invoices, customers reached, revenue per customer, and revenue per invoice.
7. **Calculate a category review score:** Combine three scaled components using configurable weights.
8. **Create charts and a findings report:** Save outputs that can be inspected or used in a portfolio write-up.

## RFM definitions and segmentation

- **Recency:** Days since the latest purchase, measured at one day after the final transaction in the dataset. A smaller number receives a higher score.
- **Frequency:** Number of distinct invoices for the customer during the data period. More invoices receive a higher score.
- **Monetary:** Total revenue after discounts during the data period. Higher revenue receives a higher score.
- **Scoring:** Each measure is ranked into quantile buckets configured in `project_config.json`. The ranking approach handles tied transaction values.
- **Segments:** Ordered business rules classify customers as Champions, At risk, Loyal customers, Potential loyalists, or Needs attention. The thresholds and rules are editable in the configuration file.

These are descriptive groups within this dataset and date range. They are not predictions or labels about a person's health or needs.

## Category review-priority score

The score is a **relative investigation aid**, not a forecast or a claim of profitability:

`Priority = 0.40 × Revenue opportunity + 0.30 × Customer reach + 0.30 × Performance gap`

Each component is scaled from 0 to 100 relative to the largest observed category value:

- **Revenue opportunity:** Category revenue relative to the highest-revenue category.
- **Customer reach:** Distinct purchasing customers relative to the category with the most customers.
- **Performance gap:** A positive gap when category revenue per purchasing customer is below the average across category-customer pairs. A larger gap receives a higher score.

The weights are editable in `project_config.json` and must sum to 1. The output also includes an equal-weight ranking so you can see whether the order depends on the selected weights. Review the component scores alongside the total; the total alone hides useful context.

The performance gap is only a prompt to investigate. The dataset does not include cost, stock availability, returns, or causal evidence. Revenue is not profit, and the score does not estimate growth.

## Outputs

After running the project:

- `data/processed/cleaned_transactions.csv`: validated line-item data
- `data/processed/data_quality_summary.json`: counts of removed or recalculated rows
- `outputs/tables/customer_rfm.csv`: customer-level metrics and segment labels
- `outputs/tables/segment_summary.csv`: customer and revenue totals by segment
- `outputs/tables/category_performance.csv`: category measures and score components
- `outputs/tables/category_priority.csv`: category ranks, score components, and equal-weight comparison
- `outputs/figures/`: monthly revenue, category revenue, and segment revenue charts
- `reports/findings.md`: generated summary, recommendations to test, and limitations

## Suggested business actions

The generated report ties recommendations to observed results. Typical actions are framed as tests:

- Review the highest-priority category’s reach and revenue-per-customer gap; test a measurable merchandising or availability change.
- Protect availability for the leading revenue category and monitor category revenue and in-stock rate.
- If an At risk customer group exists, test a win-back approach with a holdout group and compare repeat purchase rate and incremental revenue.

Treat these as hypotheses. Synthetic data cannot validate them, and customer transaction history alone does not explain customer needs.

## Configuration

Edit `project_config.json` to change:

- customer count, data period, random seed, and currency
- RFM bucket count and ordered segment rules
- score weights
- input and output paths

Change product names, categories, and prices in the product catalog CSV rather than editing analysis logic. Keep one currency in a dataset unless you add a currency-conversion step.

## Publish this project to GitHub

You mentioned that you do not have a GitHub account yet. Create one on [GitHub](https://github.com/) first, then create a new **public repository** named `pharma-retail-customer-analytics`. Do not add a second README when creating the repository.

This project folder already has a local Git repository with all project files staged. After creating the GitHub repository, use these commands. The git init and git add lines are only needed if you copy the project without its hidden .git folder. Replace the username placeholder with your GitHub username:

```bash
git init -b main
git add .
git commit -m "Add pharmacy retail analytics project"
git remote add origin https://github.com/YOUR-USERNAME/pharma-retail-customer-analytics.git
git push -u origin main
```

If Git asks for your identity, set it once with your display name and the email address associated with your GitHub account:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

The project includes a `.gitignore` that excludes virtual environments and keeps the sample synthetic data available. Do not add real pharmacy transaction files, names, contact details, prescription details, or other private customer information to a public repository.

## Next steps

1. Re-run the pipeline after changing settings and explain how the results changed.
2. Add public or organization-approved data only after checking its license and removing personal information.
3. If adding product cost, analyze gross margin separately from revenue.
4. Consider a dashboard only after the core tables and recommendations are clear.

