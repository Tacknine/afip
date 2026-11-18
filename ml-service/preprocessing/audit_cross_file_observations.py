import pandas as pd

df = pd.read_csv(
    "data/processed/maize_nps_candidates.csv",
    dtype={"household_id": str}
)

keys = [
    "household_id",
    "plot_number",
    "crop_code",
    "season"
]

cross_file = (
    df.groupby(keys)
      .agg(
          source_count=("source_file", "nunique"),
          sources=("source_file", lambda x: " | ".join(sorted(set(x)))),
          area_values=("area_harvested_acres", lambda x: list(x)),
          quantity_values=("quantity_reported", lambda x: list(x)),
          units=("quantity_unit", lambda x: list(x)),
          row_count=("source_file", "size")
      )
      .reset_index()
)

cross_file = cross_file[cross_file["source_count"] > 1]

print("\nCROSS-FILE OBSERVATIONS")
print("=" * 100)

if cross_file.empty:
    print("No cross-file observations found.")
else:
    print(cross_file.to_string(index=False))

print("\nCROSS-FILE GROUPS:", len(cross_file))
print("AUDIT COMPLETE.")
