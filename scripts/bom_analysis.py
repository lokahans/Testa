import pandas as pd
from pathlib import Path

# ==========================================
# FILE PATHS
# ==========================================

base_path = Path("/Users/hansi/Desktop/Enclustra Interview/gittestrepo/DATAtest")

bom_file = base_path / "BOM.xlsx"
avl_file = base_path / "AVL_multi_use_at_risk.xlsx"
lifecycle_file = base_path / "Lifecycle_Data_multi_use_at_risk.xlsx"

output_file = base_path / "Risk_Report.xlsx"

# ==========================================
# LOAD EXCEL FILES
# ==========================================

bom = pd.read_excel(bom_file)
avl = pd.read_excel(avl_file)
lifecycle = pd.read_excel(lifecycle_file)

# ==========================================
# STEP 1: FIND RISKY MPNs FROM LIFECYCLE DATA
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
# STEP 2: NORMALIZE AVL
# Main MPN and Alternative MPN become one common column.
# This allows the same risky MPN to be found whether it is
# listed as the main source or as an alternative.
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

main_sources["AVL Role"] = "Main"

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

alternative_sources["AVL Role"] = "Alternative"

avl_normalized = pd.concat(
    [main_sources, alternative_sources],
    ignore_index=True
)

# ==========================================
# STEP 3: MAP RISKY MPNs TO INTERNAL PNs
# ==========================================

risk_usage = risky_mpns.merge(
    avl_normalized,
    left_on=["Manufacturer", "MPN at Risk"],
    right_on=["Manufacturer", "MPN"],
    how="left"
)

# ==========================================
# STEP 4: GROUP MULTIPLE INTERNAL PNs INTO WHERE USED
# ==========================================

final_report = (
    risk_usage
    .dropna(subset=["Internal PN"])
    .groupby(["MPN at Risk", "Lifecycle Risk"], as_index=False)
    .agg({
        "Internal PN": lambda x: ", ".join(sorted(set(x)))
    })
    .rename(columns={
        "Internal PN": "Where Used"
    })
)

# ==========================================
# EXPORT REPORT
# ==========================================

final_report.to_excel(output_file, index=False)

# ==========================================
# PRINT RESULTS
# ==========================================

print("\n=== COMPONENT RISK REPORT ===\n")
print(final_report)

print(f"\nRisk report exported successfully: {output_file}")

