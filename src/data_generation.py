"""Create a reproducible synthetic pharmacy retail transaction dataset."""

import numpy as np
import pandas as pd

from src.config import load_config, project_path


def generate_transactions():
    """Generate anonymous line-item transactions using settings and the catalog."""
    config = load_config()
    dataset_settings = config["dataset"]
    generation_settings = config["generation"]
    catalog = pd.read_csv(project_path("product_catalog"))
    random_generator = np.random.default_rng(dataset_settings["random_seed"])
    start_date = pd.Timestamp(dataset_settings["start_date"])
    end_date = pd.Timestamp(dataset_settings["end_date"])
    date_count = (end_date - start_date).days + 1

    customer_ids = [
        f"C{number:05d}"
        for number in range(1, dataset_settings["customer_count"] + 1)
    ]
    profile_probabilities = generation_settings["purchase_profile_probabilities"]
    profile_names = list(profile_probabilities)
    purchase_profiles = random_generator.choice(
        profile_names,
        size=len(customer_ids),
        p=list(profile_probabilities.values()),
    )
    invoice_rates = generation_settings["purchase_profile_invoice_rates"]
    product_probabilities = catalog["sampling_weight"].astype(float).to_numpy(copy=True)
    product_probabilities /= product_probabilities.sum()
    rows = []
    invoice_number = 1

    for customer_id, profile in zip(customer_ids, purchase_profiles):
        invoice_count = max(1, int(random_generator.poisson(invoice_rates[profile])))
        invoice_days = np.sort(
            random_generator.choice(date_count, size=invoice_count, replace=True)
        )

        for day_number in invoice_days:
            invoice_id = f"INV{invoice_number:07d}"
            invoice_number += 1
            maximum_lines = min(
                generation_settings["maximum_lines_per_invoice"], len(catalog)
            )
            line_count = int(random_generator.integers(1, maximum_lines + 1))
            product_rows = random_generator.choice(
                len(catalog),
                size=line_count,
                replace=False,
                p=product_probabilities,
            )

            for product_index in product_rows:
                product = catalog.iloc[int(product_index)]
                quantity = int(
                    random_generator.choice(
                        generation_settings["quantity_values"],
                        p=generation_settings["quantity_probabilities"],
                    )
                )
                unit_price = float(product["list_price"])
                discount_rate = float(
                    random_generator.choice(
                        generation_settings["discount_rates"],
                        p=generation_settings["discount_probabilities"],
                    )
                )
                discount_amount = round(quantity * unit_price * discount_rate, 2)
                rows.append(
                    {
                        "customer_id": customer_id,
                        "invoice_id": invoice_id,
                        "transaction_date": (
                            start_date + pd.Timedelta(days=int(day_number))
                        ).date().isoformat(),
                        "product_id": product["product_id"],
                        "product_name": product["product_name"],
                        "category": product["category"],
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "discount_amount": discount_amount,
                        "line_revenue": round(
                            quantity * unit_price - discount_amount, 2
                        ),
                        "currency": dataset_settings["currency"],
                    }
                )

    transactions = pd.DataFrame(rows)
    output_path = project_path("raw_transactions")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transactions.to_csv(output_path, index=False)
    return output_path, transactions


if __name__ == "__main__":
    file_path, generated = generate_transactions()
    print(f"Created {len(generated):,} synthetic line items at {file_path}")
