import pandas as pd

df = pd.read_csv("DC_FD_ByCaseType.csv")

df["FY_year"] = (
    df["FY"]
    .astype(str)
    .str.extract(r"FY(\d{4})")        # capture 4-digit year
    .astype(int)
)

counties_of_interest = ["Anne Arundel", "Baltimore"]
df_sub = df[
    (df["County"].isin(counties_of_interest)) &
    (df["FY_year"] >= 2018)
].copy()


cases_by_year = (
    df_sub
    .groupby(["FY_year", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)

cases_by_year["diff_AA_minus_BAL"] = (
    cases_by_year["Anne Arundel"] - cases_by_year["Baltimore"]
)
cases_by_year["ratio_AA_to_BAL"] = (
    cases_by_year["Anne Arundel"] / cases_by_year["Baltimore"]
)

print("Total cases per year (2018+), by county:")
print(cases_by_year)


cases_by_category = (
    df_sub
    .groupby(["DC Case Category", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_values("Anne Arundel", ascending=False)
)

print("\nTotal cases by case CATEGORY (2018+), by county:")
print(cases_by_category)


cases_by_type = (
    df_sub
    .groupby(["DC Case Type", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_values("Anne Arundel", ascending=False)
)

print("\nTotal cases by case TYPE (2018+), by county:")
print(cases_by_type)


category_year = (
    df_sub
    .groupby(["FY_year", "DC Case Category", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)

print("\nCases by YEAR x CATEGORY x COUNTY (2018+):")
print(category_year)


type_year = (
    df_sub
    .groupby(["FY_year", "DC Case Type", "County"])["Count"]
    .sum()
    .unstack("County")
    .sort_index()
)

print("\nCases by YEAR x TYPE x COUNTY (2018+):")
print(type_year)
