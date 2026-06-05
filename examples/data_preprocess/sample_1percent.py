import os
import pandas as pd
from datasets import load_dataset, Dataset

# Paths
data_dir = os.path.expanduser("~/data/drmas_math")
train_path = os.path.join(data_dir, "train.parquet")
out_path = os.path.join(data_dir, "train_1percent.parquet")

# Load existing parquet
print(f"Loading {train_path}...")
df = pd.read_parquet(train_path)

# Sample 1% of the data
print(f"Original size: {len(df)}")
sampled_df = df.sample(frac=0.01, random_state=42)
print(f"Sampled size: {len(sampled_df)}")

# Save to new parquet
print(f"Saving to {out_path}...")
sampled_df.to_parquet(out_path, index=False)
print("Done.")
