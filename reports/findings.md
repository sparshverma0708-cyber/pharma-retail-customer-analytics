# Analysis findings

## Dataset and scope

- Data type: synthetic pharmacy retail transactions; no real customer or health information.
- Transaction period: 2025-01-01 to 2025-12-31.
- RFM analysis date: 2026-01-01 (the day after the final transaction date).
- Clean line items: 3,003.
- Customers: 300.
- Revenue after discounts: USD 28,691.98.

## Data preparation

| Measure | Rows |
|---|---:|
| Input line items | 3,003 |
| Missing or unparsed rows removed | 0 |
| Exact duplicate rows removed | 0 |
| Invalid sales rows removed | 0 |
| Revenue values recalculated | 0 |
| Clean line items | 3,003 |

## Customer segments

| Segment | Customers | Revenue | Revenue share |
|---|---:|---:|---:|
| Champions | 65 | USD 13,163.95 | 45.9% |
| Needs attention | 143 | USD 5,809.59 | 20.2% |
| Loyal customers | 37 | USD 4,821.53 | 16.8% |
| At risk | 24 | USD 2,809.07 | 9.8% |
| Potential loyalists | 31 | USD 2,087.84 | 7.3% |

## Category review priority

The score is a relative review aid built from revenue opportunity, customer reach, and a below-average revenue-per-customer gap. Component weights are editable in project_config.json. It does not predict growth or profit.

| Category | Revenue | Customers | Score / 100 | Rank |
|---|---:|---:|---:|---:|
| Personal Care | USD 2,998.83 | 203 | 76.7 | 1 |
| Cold and Allergy | USD 3,777.92 | 219 | 71.7 | 2 |
| Vitamins | USD 6,350.99 | 212 | 69.0 | 3 |
| First Aid | USD 4,442.91 | 200 | 55.4 | 4 |
| Digestive Health | USD 3,331.05 | 174 | 53.4 | 5 |
| OTC Pain Relief | USD 4,149.99 | 198 | 53.3 | 6 |
| Wellness Accessories | USD 3,640.29 | 167 | 45.8 | 7 |

The highest revenue category is **Vitamins**. The first category to review under the configured score is **Personal Care**. Compare the configured ranking with the equal-weight ranking in outputs/tables/category_priority.csv; a ranking change indicates weight sensitivity.

## Suggested actions to test

1. **Review Personal Care first.** It ranks 1 on the configured review score (76.7/100). Inspect customer reach and the revenue-per-customer gap, then test a small, measurable merchandising or availability change.
2. **Protect the leading category.** Vitamins contributes 22.1% of observed revenue. Review stock availability and monitor category revenue and in-stock rate.
3. **Test a customer win-back.** The rule-based At risk segment has 24 customers and USD 2,809.07 in historical period revenue. Use a holdout group and compare repeat purchase rate and incremental revenue before expanding any offer.
These are hypotheses for business testing, not guaranteed outcomes. Transaction history alone does not explain customer needs or support medical advice.

## Limitations

- All records are synthetic and illustrate a workflow only; they do not establish real pharmacy behavior.
- Revenue is not profit. Product cost, returns, stock availability, and operating costs are not included.
- RFM segments are descriptive rules for the selected period, not customer identities or predictions.
- Category comparisons can reflect the synthetic data-generation choices and the selected date range.
