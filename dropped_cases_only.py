import pandas as pd

df = pd.read_csv("DC_FD_ByCaseType.csv")

# Extract FY year (e.g., FY2019 → 2019)
df["FY_year"] = (
    df["FY"]
      .astype(str)
      .str.extract(r"FY(\d{4})")
      .astype(int)
)

# Restrict analysis to Anne Arundel Baltimore city and Baltimore County
counties = ["Anne Arundel", "Baltimore City", "Baltimore", "Prince George's"]
df2 = df[df["County"].isin(counties)]


nolle = df2[
    df2["Filing/Disposition Type"].str.contains("Nolle", case=False, na=False)
].copy()


nolle_by_year = (
    nolle
    .groupby(["FY_year", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)
print(nolle_by_year)


nolle_by_category = (
    nolle
    .groupby(["DC Case Category", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_values("Anne Arundel", ascending=False)
)
print(nolle_by_category)


nolle_by_type = (
    nolle
    .groupby(["DC Case Type", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_values("Anne Arundel", ascending=False)
)
print(nolle_by_type)



# Total filings (all filing types)
filings = (
    df2[df2["Count Description"] == "Filing"]
    .groupby(["FY_year", "County"])["Count"]
    .sum()
)

# Nolle pros totals
nolle_totals = (
    nolle
    .groupby(["FY_year", "County"])["Count"]
    .sum()
)

# Calculate percent of filings that end in nolle prosequi
nolle_rate = (nolle_totals / filings * 100).unstack("County").sort_index()
print(nolle_rate)


nolle_cat_year = (
    nolle
    .groupby(["FY_year", "DC Case Category", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)
print(nolle_cat_year)


nolle_type_year = (
    nolle
    .groupby(["FY_year", "DC Case Type", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)
print(nolle_type_year)


population = {
    "Anne Arundel": 600000,
    "Baltimore": 850000,
    "Baltimore City": 575000,
    "Prince George's": 965000
    
}

nolle_per_capita = nolle_by_year.copy()
for county in counties:
    nolle_per_capita[county] = nolle_per_capita[county] / population[county] * 100000

print(nolle_per_capita)




#--------------------------------------------------------------------
# Graphs
import matplotlib.pyplot as plt

# nolle_rate already exists from your script (percentage dropped)

plt.figure(figsize=(10,6))
for county in counties:
    plt.plot(nolle_rate.index, nolle_rate[county], marker='o', label=county)

plt.title("Dismissal Rate Comparison (% of Filings Dropped)")
plt.xlabel("Year")
plt.ylabel("Nolle Pros Rate (%)")
plt.grid(True, linestyle='--', alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()


# Filter for Criminal category only
criminal_nolle = nolle[nolle["DC Case Category"] == "Criminal"]



criminal_by_year = (
    criminal_nolle.groupby(["FY_year", "County"])["Count"]
    .sum()
    .unstack("County")
)

plt.figure(figsize=(10,6))
for county in counties:
    plt.plot(criminal_by_year.index, criminal_by_year[county], marker='o', label=county)

plt.title("Criminal Cases Dropped (Nolle Pros) per Year")
plt.xlabel("Year")
plt.ylabel("Criminal Nolle Pros Count")
plt.grid(True, linestyle='--', alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()


import numpy as np

# Convert category table into heatmap array
cat_data = nolle_by_category[counties].values  # rows=categories, cols=counties

plt.figure(figsize=(8,6))
plt.imshow(cat_data, cmap="Reds", aspect="auto")
plt.title("Heatmap: Dropped Cases by Category (Higher = Worse Performance)")
plt.yticks(range(len(nolle_by_category.index)), nolle_by_category.index)
plt.xticks(range(len(counties)), counties)
plt.colorbar(label="Total Nolle Pros")
plt.tight_layout()
plt.show()


# Calculate the gap for percent dropped
gap = nolle_rate["Anne Arundel"] - nolle_rate["Baltimore"]

plt.figure(figsize=(10,6))
plt.plot(gap.index, gap, marker='o', color='red')
plt.axhline(0, color='black', linewidth=1)
plt.title("Performance Gap: Anne Arundel vs Baltimore County (% Dropped)")
plt.xlabel("Year")
plt.ylabel("AA – BAL (Percentage Points)")
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()
plt.show()

# Calculate the gap for percent dropped
gap = nolle_rate["Anne Arundel"] - nolle_rate["Baltimore City"]

plt.figure(figsize=(10,6))
plt.plot(gap.index, gap, marker='o', color='red')
plt.axhline(0, color='black', linewidth=1)
plt.title("Performance Gap: Anne Arundel vs Baltimore City (% Dropped)")
plt.xlabel("Year")
plt.ylabel("AA – BAL (Percentage Points)")
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()
plt.show()

# Calculate the gap for percent dropped
gap = nolle_rate["Anne Arundel"] - nolle_rate["Prince George's"]

plt.figure(figsize=(10,6))
plt.plot(gap.index, gap, marker='o', color='red')
plt.axhline(0, color='black', linewidth=1)
plt.title("Performance Gap: Anne Arundel vs Prince George (% Dropped)")
plt.xlabel("Year")
plt.ylabel("AA – BAL (Percentage Points)")
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()
plt.show()






# Filter for Criminal category only
motor_vehicle_nolle = nolle[nolle["DC Case Category"] == "Motor Vehicle"]




mv_nolle_by_year = (
    motor_vehicle_nolle.groupby(["FY_year", "County"])["Count"]
    .sum()
    .unstack("County")
)

mv_filings = (
    df2[
        (df2["DC Case Category"] == "Motor Vehicle") &
        (df2["Count Description"] == "Filing")
    ]
    .groupby(["FY_year", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)

mv_nolle_rate = (mv_nolle_by_year / mv_filings) * 100

plt.figure(figsize=(10,6))
for county in mv_nolle_by_year.columns:
    plt.plot(mv_nolle_by_year.index, mv_nolle_by_year[county], marker='o', label=county)

plt.title("Motor Vehicle Cases Dropped (Nolle Pros) per Year")
plt.xlabel("Year")
plt.ylabel("Dropped Motor Vehicle Cases")
plt.grid(True, linestyle='--', alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()

plt.figure(figsize=(10,6))
for county in mv_nolle_rate.columns:
    plt.plot(mv_nolle_rate.index, mv_nolle_rate[county], marker='o', label=county)

plt.title("Motor Vehicle Dismissal Rate (% Dropped)")
plt.xlabel("Year")
plt.ylabel("% of Motor Vehicle Filings Dropped")
plt.grid(True, linestyle='--', alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()

gap_mv_bal = mv_nolle_rate["Anne Arundel"] - mv_nolle_rate["Baltimore"]

plt.figure(figsize=(10,6))
plt.plot(gap_mv_bal.index, gap_mv_bal, marker='o', color='red')
plt.axhline(0, color='black', linewidth=1)
plt.title("Performance Gap (Motor Vehicle): Anne Arundel vs Baltimore County")
plt.xlabel("Year")
plt.ylabel("AA - BAL (% Points Dropped)")
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()
plt.show()

gap_mv_city = mv_nolle_rate["Anne Arundel"] - mv_nolle_rate["Baltimore City"]

plt.figure(figsize=(10,6))
plt.plot(gap_mv_city.index, gap_mv_city, marker='o', color='red')
plt.axhline(0, color='black', linewidth=1)
plt.title("Performance Gap (Motor Vehicle): Anne Arundel vs Baltimore City")
plt.xlabel("Year")
plt.ylabel("AA - City (% Points Dropped)")
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()
plt.show()

gap_mv_city = mv_nolle_rate["Anne Arundel"] - mv_nolle_rate["Prince George's"]

plt.figure(figsize=(10,6))
plt.plot(gap_mv_city.index, gap_mv_city, marker='o', color='red')
plt.axhline(0, color='black', linewidth=1)
plt.title("Performance Gap (Motor Vehicle): Anne Arundel vs Prince George's")
plt.xlabel("Year")
plt.ylabel("AA - City (% Points Dropped)")
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()
plt.show()
