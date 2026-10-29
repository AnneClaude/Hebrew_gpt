import os
from datasets import load_dataset

RAW_DIR = os.path.join("data", "raw")
OUTPUT_PATH = os.path.join(RAW_DIR, "hewiki.parquet")


def main():
    # to make sure the output folder exists
    os.makedirs(RAW_DIR, exist_ok=True)

    # download Hebrew Wikipedia (snapshot from Nov 2023)
    print("Downloading Hebrew Wikipedia...")
    ds = load_dataset("wikimedia/wikipedia", "20231101.he", split="train")

    # inspect it
    print(f"Number of articles: {len(ds):,}")
    print(f"Fields: {ds.column_names}")
    print("\nExample title:", ds[0]["title"])
    print("Example text (first 300 chars):")
    print(ds[0]["text"][:300])

    # save to disk
    ds.to_parquet(OUTPUT_PATH)
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()