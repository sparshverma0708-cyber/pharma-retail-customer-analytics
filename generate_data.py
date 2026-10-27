"""Generate the included synthetic line-item dataset from the product catalog."""

from src.data_generation import generate_transactions


if __name__ == "__main__":
    output_path, generated = generate_transactions()
    print(f"Generated {len(generated):,} line items in {output_path}")
