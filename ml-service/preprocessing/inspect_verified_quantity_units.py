from pathlib import Path
import pyreadstat

ROOT = Path(
    "data/raw/nbs/nps2019/"
    "TZA_2019_NPD-SDD_v06_M_STATA12"
)

configs = {
    "AG_SEC_4A": ("AG_SEC_4A.dta", "ag4a_27"),
    "AG_SEC_4B": ("AG_SEC_4B.dta", "ag4b_28"),
}

for module, (filename, variable) in configs.items():

    df, meta = pyreadstat.read_dta(str(ROOT / filename))

    index = meta.column_names.index(variable)

    print("\n" + "=" * 70)
    print(module)
    print("=" * 70)

    print("Variable:", variable)
    print("Label:", meta.column_labels[index])

    print("\nVariable format:")
    print(meta.original_variable_types.get(variable))

    print("\nStorage type:")
    print(df[variable].dtype)

    print("\nAll maize quantity statistics:")
    print(df.loc[df["cropid"] == 11, variable].describe())

    print("\nFirst 20 maize quantities:")
    print(
        df.loc[df["cropid"] == 11,
               ["sdd_hhid", "plotnum", "cropid", variable]]
        .head(20)
        .to_string(index=False)
    )

print("\nQUANTITY UNIT INVESTIGATION COMPLETE.")
