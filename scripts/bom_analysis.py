import pandas as pd
from pathlib import Path

# ==========================================
# SELECT DATA FOLDER
# ==========================================

folder_selected = input(
    "Drag the data folder here and press Enter: "
).strip()

# Remove quotes if macOS adds them
folder_selected = folder_selected.strip("'").strip('"')

base_path = Path(folder_selected)

if not base_path.exists():
    raise FileNotFoundError(
        f"Folder does not exist: {base_path}"
    )

print(f"\nSelected folder: {base_path}")

# ==========================================
# FIND INPUT FILES AUTOMATICALLY
# ==========================================

bom_files = list(base_path.glob("*BOM*.xlsx"))

avl_files = list(
    base_path.glob("*AVL_multi_use_at_risk*.xlsx")
)

lifecycle_files = list(
    base_path.glob("*Lifecycle_Data_multi_use_at_risk*.xlsx")
)

# ==========================================
# VALIDATE FILES
# ==========================================

if not bom_files:
    raise FileNotFoundError(
        "No BOM Excel file found."
    )

if not avl_files:
    raise FileNotFoundError(
        "No AVL multi-use Excel file found."
    )

if not lifecycle_files:
    raise FileNotFoundError(
        "No Lifecycle multi-use Excel file found."
    )

# ==========================================
# USE FIRST MATCHING FILE
# ==========================================

bom_file = bom_files[0]
avl_file = avl_files[0]
lifecycle_file = lifecycle_files[0]

print(f"\nBOM file used: {bom_file.name}")
print(f"AVL file used: {avl_file.name}")
print(f"Lifecycle file used: {lifecycle_file.name}")

# ==========================================
# LOAD EXCEL FILES
# ==========================================

bom = pd.read_excel(bom_file)
avl = pd.read_excel(avl_file)
lifecycle = pd.read_excel(lifecycle_file)

# ==========================================
# FIND RISKY MPNs
# ==========================================

risk_status = ["NRND", "EOL"]

risky_mpns = lifecycle[
    lifecycle["Lifecycle Status"].isin(risk_status)
].copy()

risky_mpns = risky_mpns.rename(columns={
    "Vendor": "Manufacturer",
    "PN": "MPN at Risk",
    "Lifecycle Status": "Lifecycle Risk"
})

# ==========================================
# NORMALIZE AVL
# Main and Alternative sources become one table
# ==========================================

main_sources = avl[[
    "PN",
    "Manufacturer",
    "Manufacturer PN"
]].copy()

main_sources = main_sources.rename(columns={
    "PN": "Internal PN",
    "Manufacturer PN": "MPN"
})

alternative_sources = avl[[
    "PN",
    "Alternative Vendor",
    "Alternative PN"
]].copy()

alternative_sources = alternative_sources.rename(columns={
    "PN": "Internal PN",
    "Alternative Vendor": "Manufacturer",
    "Alternative PN": "MPN"
})

# Combine main and alternative sources
avl_normalized = pd.concat(
    [main_sources, alternative_sources],
    ignore_index=True
)

# ==========================================
# MAP RISKY MPNs TO INTERNAL PNs
# ==========================================

risk_usage = risky_mpns.merge(
    avl_normalized,
    left_on=["Manufacturer", "MPN at Risk"],
    right_on=["Manufacturer", "MPN"],
    how="left"
)

# ==========================================
# CREATE FINAL REPORT
# ==========================================

final_report = (
    risk_usage
    .dropna(subset=["Internal PN"])
    .groupby(
        ["MPN at Risk", "Lifecycle Risk"],
        as_index=False
    )
    .agg({
        "Internal PN": lambda x:
            ", ".join(sorted(set(x)))
    })
    .rename(columns={
        "Internal PN": "Where Used"
    })
)

# ==========================================
# EXPORT REPORT
# ==========================================

output_file = base_path / "Risk_Report.xlsx"

final_report.to_excel(
    output_file,
    index=False
)

# ==========================================
# PRINT RESULTS
# ==========================================

print("\n=== COMPONENT RISK REPORT ===\n")

print(final_report)

print(
    f"\nRisk report exported successfully:\n{output_file}"
)