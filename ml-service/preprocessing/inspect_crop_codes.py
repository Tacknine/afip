from pathlib import Path
import pyreadstat

root = Path("data/raw")

for path in root.rglob("*.dta"):
    if "AG_SEC_4A" not in path.name.upper() and "AG_SEC_4B" not in path.name.upper():
        continue

    print("\n================================")
    print("FILE:", path)

    try:
        df, meta = pyreadstat.read_dta(str(path))

        print("COLUMNS:", df.columns.tolist())

        for col in df.columns:
            if "crop" in col.lower():
                print("\nCROP COLUMN:", col)
                print("VALUE LABELS:")
                print(meta.variable_value_labels.get(col, {}))
                print("OBSERVED VALUES:")
                print(df[col].value_counts(dropna=False).head(100).to_string())

    except Exception as e:
        print("ERROR:", e)
