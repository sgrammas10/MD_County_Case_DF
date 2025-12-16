import pandas as pd
import matplotlib.pyplot as plt

# ======================
# 1. Load and prepare data
# ======================

df = pd.read_csv("DC_FD_ByCaseType.csv")

# Extract numeric FY year (FY2025 -> 2025)
df["FY_year"] = (
    df["FY"]
    .astype(str)
    .str.extract(r"FY(\d{4})")
    .astype(int)
)

# Filter to DUI only
df_dui = df[df["DC Case Type"].str.contains("DUI", case=False, na=False)]

# Filter to Anne Arundel County
df_dui_aa = df_dui[df_dui["County"] == "Anne Arundel"].copy()

# ======================
# 2. Define which disposition labels count as FAILURES
# ======================

# Success outcomes: DO NOT count as failures
success_terms = ["Guilty", "Not Guilty", "Probation"]

# Failure outcomes: DO count as failures
# -> adjust this list if you want to include/exclude "Jury Trial", "Withdrawn", etc.
failure_terms = ["Nolle", "Stet", "Dismiss"]

# ======================
# 3. Denominator: total DUI filings per year
# ======================

dui_filings_by_year = (
    df_dui_aa[df_dui_aa["Count Description"] == "Filing"]
    .groupby("FY_year")["Count"]
    .sum()
)

# ======================
# 4. Numerator: DUI failures per year (explicit failure labels)
# ======================

# Only look at final disposition rows
dui_dispositions = df_dui_aa[df_dui_aa["Count Description"] == "Disposition"]

# Rows where disposition matches any of the failure terms
failure_mask = dui_dispositions["Filing/Disposition Type"].str.contains(
    "|".join(failure_terms),
    case=False,
    na=False
)

dui_failures_by_year = (
    dui_dispositions[failure_mask]
    .groupby("FY_year")["Count"]
    .sum()
)

# Align indices
dui_failures_by_year = dui_failures_by_year.reindex(dui_filings_by_year.index, fill_value=0)

# ======================
# 5. Compute failure rate
# ======================

dui_failure_rate = (dui_failures_by_year / dui_filings_by_year) * 100
dui_failure_rate = dui_failure_rate.fillna(0)

results = pd.DataFrame({
    "Total DUI Filings": dui_filings_by_year,
    "Total DUI Failures": dui_failures_by_year,
    "Failure Rate (%)": dui_failure_rate.round(3),
})

print("\nAnne Arundel County DUI Failure Results")
print(results)

# ======================
# 6. Plot
# ======================

plt.figure(figsize=(10, 6))
plt.plot(results.index, results["Failure Rate (%)"], marker='o')
plt.title("Anne Arundel DUI Failure Rate\n(% of Filings Ending in Nolle Pros / Stet / Dismissed)")
plt.xlabel("Fiscal Year")
plt.ylabel("Failure Rate (%)")
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
