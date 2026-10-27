"""Create browser-friendly SVG charts from the analysis results."""

from html import escape

import pandas as pd

from src.config import load_config, project_path


CHART_WIDTH = 960
CHART_COLOR = "#247b8b"
TEXT_COLOR = "#20323a"
GRID_COLOR = "#d9e2e5"


def create_charts(transactions, segment_summary, category_summary):
    """Save monthly revenue, category revenue, and segment revenue charts."""
    currency = load_config()["dataset"]["currency"]
    transactions = transactions.copy()
    transactions["transaction_date"] = pd.to_datetime(
        transactions["transaction_date"]
    )
    monthly_revenue = (
        transactions.set_index("transaction_date")
        .resample("MS")["line_revenue"]
        .sum()
    )
    _save_line_chart(
        monthly_revenue,
        project_path("monthly_revenue_figure"),
        "Monthly revenue",
        currency,
    )
    _save_bar_chart(
        category_summary,
        "category",
        "revenue",
        project_path("category_revenue_figure"),
        "Revenue by category",
        currency,
    )
    _save_bar_chart(
        segment_summary,
        "segment",
        "total_revenue",
        project_path("segment_revenue_figure"),
        "Revenue by customer segment",
        currency,
    )


def _svg_start(width, height, title):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="36" y="36" fill="{TEXT_COLOR}" font-family="Arial, sans-serif" font-size="22" font-weight="bold">{escape(title)}</text>',
    ]


def _save_line_chart(values, output_path, title, currency):
    width, height = CHART_WIDTH, 500
    left, right, top, bottom = 76, 28, 72, 78
    plot_width, plot_height = width - left - right, height - top - bottom
    minimum, maximum = float(values.min()), float(values.max())
    value_range = maximum - minimum or 1.0
    points = []
    for index, value in enumerate(values):
        x = left + (plot_width * index / max(len(values) - 1, 1))
        y = top + plot_height - (float(value) - minimum) / value_range * plot_height
        points.append((x, y))

    parts = _svg_start(width, height, title)
    for fraction in (0, 0.25, 0.5, 0.75, 1):
        y = top + plot_height * fraction
        label_value = maximum - value_range * fraction
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="{GRID_COLOR}"/>')
        parts.append(f'<text x="{left-10}" y="{y+5:.1f}" text-anchor="end" fill="{TEXT_COLOR}" font-family="Arial, sans-serif" font-size="12">{label_value:,.0f}</text>')

    point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    parts.append(f'<polyline points="{point_string}" fill="none" stroke="{CHART_COLOR}" stroke-width="3"/>')
    for (x, y), month in zip(points, values.index):
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{CHART_COLOR}"/>')
        parts.append(f'<text x="{x:.1f}" y="{height-bottom+25}" text-anchor="middle" fill="{TEXT_COLOR}" font-family="Arial, sans-serif" font-size="12">{escape(month.strftime("%b %Y"))}</text>')
    parts.append(f'<text x="{left}" y="{height-20}" fill="{TEXT_COLOR}" font-family="Arial, sans-serif" font-size="13">Revenue ({escape(currency)})</text>')
    parts.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts), encoding="utf-8")


def _save_bar_chart(data, label_column, value_column, output_path, title, currency):
    rows = list(data.sort_values(value_column, ascending=False).itertuples(index=False))
    width = CHART_WIDTH
    row_height, top, bottom, left, right = 42, 76, 46, 225, 100
    height = top + row_height * len(rows) + bottom
    plot_width = width - left - right
    maximum = float(data[value_column].max()) or 1.0
    parts = _svg_start(width, height, title)

    for row_index, row in enumerate(rows):
        y = top + row_index * row_height
        label = escape(str(getattr(row, label_column)))
        value = float(getattr(row, value_column))
        bar_width = value / maximum * plot_width
        parts.append(f'<text x="{left-12}" y="{y+23}" text-anchor="end" fill="{TEXT_COLOR}" font-family="Arial, sans-serif" font-size="14">{label}</text>')
        parts.append(f'<rect x="{left}" y="{y+5}" width="{bar_width:.1f}" height="26" rx="3" fill="{CHART_COLOR}"/>')
        parts.append(f'<text x="{left+bar_width+8:.1f}" y="{y+23}" fill="{TEXT_COLOR}" font-family="Arial, sans-serif" font-size="13">{escape(currency)} {value:,.0f}</text>')
    axis_y = top + row_height * len(rows)
    parts.append(f'<line x1="{left}" y1="{axis_y}" x2="{width-right}" y2="{axis_y}" stroke="{GRID_COLOR}"/>')
    parts.append(f'<text x="{left}" y="{height-16}" fill="{TEXT_COLOR}" font-family="Arial, sans-serif" font-size="13">Revenue ({escape(currency)})</text>')
    parts.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts), encoding="utf-8")
