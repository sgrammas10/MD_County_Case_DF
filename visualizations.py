import pandas as pd
import matplotlib.pyplot as plt

# ========= 1. LOAD & PREP DATA =========

# Path to your CSV
CSV_PATH = "DC_FD_ByCaseType.csv"

df = pd.read_csv(CSV_PATH)

# Extract numeric fiscal year: "FY2018" -> 2018
df["FY_year"] = (
    df["FY"]
    .astype(str)
    .str.extract(r"FY(\d{4})")
    .astype(int)
)

# Focus on the three jurisdictions
counties = ["Anne Arundel", "Baltimore", "Baltimore City"]
df = df[df["County"].isin(counties)]

# Nolle Pros rows
mask_nolle = df["Filing/Disposition Type"].str.contains("Nolle", case=False, na=False)
nolle = df[mask_nolle].copy()

# Total filings (all filing records)
filings = (
    df[df["Count Description"] == "Filing"]
    .groupby(["FY_year", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)

# Total Nolle Pros counts
nolle_by_year = (
    nolle
    .groupby(["FY_year", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)

# Make sure both tables share the same years/index
filings = filings.loc[nolle_by_year.index]

# ========= 2. PER-CAPITA & RATES =========

# Replace these with the most accurate population estimates you want to use
population = {
    "Anne Arundel": 600000,
    "Baltimore": 850000,        # Baltimore County
    "Baltimore City": 570000,   # Baltimore City
}

# Per 100k population
per_capita = nolle_by_year.copy()
for county in per_capita.columns:
    per_capita[county] = per_capita[county] / population[county] * 100000

# Percent of filings that were Nolle Pros
nolle_rate = (nolle_by_year / filings) * 100

# ========= 3. LINE CHART: TOTAL DROPPED CASES =========

plt.figure(figsize=(10, 5))

for county in counties:
    plt.plot(nolle_by_year.index, nolle_by_year[county], label=county)

plt.xlabel("Fiscal Year")
plt.ylabel("Nolle Pros (Dropped Cases)")
plt.title("Total Dropped Cases by Year")
plt.legend()
plt.tight_layout()
plt.show()

# ========= 4. HEATMAP: DROPPED CASES PER 100K POP =========

plt.figure(figsize=(12, 4))

heat_data_pc = per_capita.values  # rows = counties, cols = years
plt.imshow(heat_data_pc, aspect="auto")

plt.yticks(range(len(counties)), counties)
plt.xticks(range(len(per_capita.index)), per_capita.index, rotation=45)
plt.colorbar(label="Dropped Cases per 100,000 Population")
plt.title("Heatmap: Dropped Cases Per 100k Population")
plt.tight_layout()
plt.show()

# ========= 5. HEATMAP: % OF FILINGS DROPPED =========

plt.figure(figsize=(12, 4))

heat_data_rate = nolle_rate.values
plt.imshow(heat_data_rate, aspect="auto")

plt.yticks(range(len(counties)), counties)
plt.xticks(range(len(nolle_rate.index)), nolle_rate.index, rotation=45)
plt.colorbar(label="Percent of Filings that were Nolle Pros")
plt.title("Heatmap: Nolle Pros Rate (% of Filings Dropped)")
plt.tight_layout()
plt.show()
