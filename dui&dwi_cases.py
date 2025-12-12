import pandas as pd
import matplotlib.pyplot as plt

# ======================
# 1. Load and prepare data
# ======================

df = pd.read_csv("DC_FD_ByCaseType.csv")

# Extract numeric FY year
df["FY_year"] = (
    df["FY"]
    .astype(str)
    .str.extract(r"FY(\d{4})")
    .astype(int)
)

# Filter to DUI only
df_dui = df[df["DC Case Type"].str.contains("DUI", case=False, na=False)]

# Filter to Anne Arundel County
df_dui_aa = df_dui[df_dui["County"] == "Anne Arundel"].copy()  # .copy() avoids the warning

# ======================
# 2. Define SUCCESS outcomes (NOT counted as failures)
# ======================

# If any of these strings appear in Filing/Disposition Type, we treat that as a "successful" outcome
success_terms = [
    "Guilty",
    "Not Guilty",
    "Probation Before Judgment",
]

# Create a boolean column: is_success
df_dui_aa["is_success"] = df_dui_aa["Filing/Disposition Type"].str.contains(
    "|".join(success_terms),
    case=False,
    na=False
)

# ======================
# 3. Build denominator: total DUI filings per year
# ======================

dui_total_by_year = (
    df_dui_aa[df_dui_aa["Count Description"] == "Filing"]
    .groupby("FY_year")["Count"]
    .sum()
)

# ======================
# 4. Build numerator: DUI failures = all dispositions that are NOT success
# ======================

# Consider only non-filing rows as outcome rows
dui_outcomes = df_dui_aa[df_dui_aa["Count Description"] != "Filing"]

# Failures: outcome rows that are NOT success
dui_failures = dui_outcomes[~dui_outcomes["is_success"]]

dui_failure_by_year = (
    dui_failures
    .groupby("FY_year")["Count"]
    .sum()
)

# Align indices so division works safely
dui_failure_by_year = dui_failure_by_year.reindex(dui_total_by_year.index, fill_value=0)

# ======================
# 5. Compute failure rate and display table
# ======================

dui_failure_rate = (dui_failure_by_year / dui_total_by_year) * 100
dui_failure_rate = dui_failure_rate.fillna(0)

results = pd.DataFrame({
    "Total DUI Filings": dui_total_by_year,
    "Total DUI Failures (Non-G/NG/PBJ)": dui_failure_by_year,
    "Failure Rate (%)": dui_failure_rate
})

print("\nAnne Arundel County DUI Failure Results (Non-Guilty / Non-Not-Guilty / Non-PBJ):")
print(results)

# ======================
# 6. Plot the failure rate over time
# ======================

plt.figure(figsize=(10,6))
plt.plot(results.index, results["Failure Rate (%)"], marker='o', color='red')

plt.title("Anne Arundel DUI Failure Rate\n(% of DUI Filings NOT Ending in Guilty / Not Guilty / PBJ)")
plt.xlabel("Fiscal Year")
plt.ylabel("Failure Rate (%)")
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
