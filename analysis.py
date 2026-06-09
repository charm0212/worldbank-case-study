import tomllib
import pandas as pd
import numpy as np

# 1. READ CONFIG
with open("config.toml", "rb") as f:
    config = tomllib.load(f)

start_year = config["time"]["start_year"]
end_year = config["time"]["end_year"]
ind_key = config["series"]["industry_value_added_usd_const"]
man_key = config["series"]["manufacturing_value_added_usd_const"]
gdp_key = config["series"]["gdp_usd_real"]


# 2. READ LOCAL CSV
try:
    df_wide = pd.read_csv("output_wide.csv")
except FileNotFoundError:
    print("Error: output_wide.csv not found. Run main.py first.")
    exit(1)


# 3. HELPER
def get_value_with_fallback(series_row, target_year, min_year):
    # Backward scanning to handle missing observations
    if series_row is None:
        return None, np.nan
    for year in range(target_year, min_year - 1, -1):
        col_name = f"year_{year}"
        if col_name in series_row.index:
            value = series_row[col_name]
            if pd.notna(value):
                return year, value
    return None, np.nan

def calculate_share(value_added, gdp):
    # Compute value-added shares
    if pd.notna(value_added) and pd.notna(gdp) and gdp > 0:
        return value_added / gdp
    return np.nan

def calculate_cagr(start_value, end_value, start_year, end_year):
    # Compute long-term CAGR
    if (
    pd.notna(start_value)
    and pd.notna(end_value)
    and start_value > 0
    and end_year > start_year
    ):
        return (end_value / start_value) ** (1 / (end_year - start_year)) - 1
    return np.nan


# 4. DATA PROCESSING
summary_rows = []
for country_code in df_wide['country'].unique():
    c_df = df_wide[df_wide['country'] == country_code].set_index('indicator')
    row = {"country": country_code}

    ind_row = c_df.loc[ind_key] if ind_key in c_df.index else None
    man_row = c_df.loc[man_key] if man_key in c_df.index else None
    gdp_row = c_df.loc[gdp_key] if gdp_key in c_df.index else None
    
    # Start year value-added shares (Year 2020)
    _, ind_start_value = get_value_with_fallback(ind_row, start_year, start_year)
    _, man_start_value = get_value_with_fallback(man_row, start_year, start_year)
    _, gdp_start_value = get_value_with_fallback(gdp_row, start_year, start_year)

    row[f"industry_share_{start_year}"] = calculate_share(ind_start_value, gdp_start_value)
    row[f"manufacturing_share_{start_year}"] = calculate_share(man_start_value, gdp_start_value)
    
    # End year value-added shares (Year 2025: returns NaN)
    v_ind_end = ind_row[f"year_{end_year}"] if ind_row is not None and f"year_{end_year}" in ind_row.index else np.nan
    v_man_end = man_row[f"year_{end_year}"] if man_row is not None and f"year_{end_year}" in man_row.index else np.nan
    v_gdp_end = gdp_row[f"year_{end_year}"] if gdp_row is not None and f"year_{end_year}" in gdp_row.index else np.nan

    row[f"industry_share_{end_year}"] = calculate_share(v_ind_end, v_gdp_end)
    row[f"manufacturing_share_{end_year}"] = calculate_share(v_man_end, v_gdp_end)

    # Dynamic fallback end year tracking (finds latest valid data)
    latest_gdp_year, latest_gdp_value = get_value_with_fallback(gdp_row, end_year, start_year + 1)
    latest_ind_year, latest_ind_value = get_value_with_fallback(ind_row, end_year, start_year + 1)
    latest_man_year, latest_man_value = get_value_with_fallback(man_row, end_year, start_year + 1)

    ## Latest valid year for industry share
    gdp_matching_ind = gdp_row[f"year_{latest_ind_year}"] if gdp_row is not None and latest_ind_year and f"year_{latest_ind_year}" in gdp_row.index else np.nan
    if latest_ind_year:
        row[f"industry_share_{latest_ind_year}"] = calculate_share(latest_ind_value, gdp_matching_ind)
   
    ## Latest valid year for manufacturing share
    gdp_matching_man = gdp_row[f"year_{latest_man_year}"] if gdp_row is not None and latest_man_year and f"year_{latest_man_year}" in gdp_row.index else np.nan
    if latest_man_year:
        row[f"manufacturing_share_{latest_man_year}"] = calculate_share(latest_man_value, gdp_matching_man)

    # CAGR calculations
    row[f"gdp_cagr_{start_year}_{latest_gdp_year}"] = calculate_cagr(gdp_start_value, latest_gdp_value, start_year, latest_gdp_year) if latest_gdp_year else np.nan
    row[f"industry_cagr_{start_year}_{latest_ind_year}"] = calculate_cagr(ind_start_value, latest_ind_value, start_year, latest_ind_year) if latest_ind_year else np.nan
    row[f"manufacturing_cagr_{start_year}_{latest_man_year}"] = calculate_cagr(man_start_value, latest_man_value, start_year, latest_man_year) if latest_man_year else np.nan
    
    summary_rows.append(row)
    

# 5. EXPORT RESULTS
summary_table = pd.DataFrame(summary_rows)

# Print the summary table
print("\n--- SUMMARY TABLE PREVIEW ---")
print(summary_table.to_string(index=False))

# Save the csv file
summary_table.to_csv("summary_table.csv", index=False, float_format="%.6f")
print("Successfully generated summary_table.csv")


# 6. AUTOMATED ANALYSIS & INTERPRETATION
print("\n" + "="*50)
print("          DATA ANALYSIS INTERPRETATION          ")
print("="*50)

# Extract table column headers
mfg_share_col = [c for c in summary_table.columns if c.startswith("manufacturing_share_") and c not in [f"manufacturing_share_{start_year}", f"manufacturing_share_{end_year}"]][0]
ind_share_col = [c for c in summary_table.columns if c.startswith("industry_share_") and c not in [f"industry_share_{start_year}", f"industry_share_{end_year}"]][0]
gdp_cagr_col = [c for c in summary_table.columns if c.startswith("gdp_cagr_")][0]
ind_cagr_col = [c for c in summary_table.columns if c.startswith("industry_cagr_")][0]
mfg_cagr_col = [c for c in summary_table.columns if c.startswith("manufacturing_cagr_")][0]


# Q1: Which countries show signs of de‐industrialization?
# Methodology:
# (1) Primary Filter: Manufacturing share of GDP declined (Share Delta < 0)
# (2) Contextual Check: Did total industry share also decline?
# (3) Secondary Validation: Is manufacturing shrinking absolutely (CAGR < 0) or relatively (CAGR >= 0)?

mfg_share_changes = {}
ind_share_changes = {}

# Step 1: Calculate all deltas first
for _, r in summary_table.iterrows():
    country = r["country"]
    if pd.notna(r[f"manufacturing_share_{start_year}"]) and pd.notna(r[mfg_share_col]):
        mfg_share_changes[country] = r[mfg_share_col] - r[f"manufacturing_share_{start_year}"]
        
    if pd.notna(r[f"industry_share_{start_year}"]) and pd.notna(r[ind_share_col]):
        ind_share_changes[country] = r[ind_share_col] - r[f"industry_share_{start_year}"]

# Step 2: Apply primary filter (countries with declined manufacturing share)
mfg_change_series = pd.Series(mfg_share_changes)
de_ind_countries = mfg_change_series[mfg_change_series < 0].sort_values(ascending=True)

print("\n1. Countries with signs of de-industrialization (Manufacturing share declined):")

# Step 3: Extract values and determine logic for each de-industrializing country
for c_code, mfg_delta_val in de_ind_countries.items():
    
    c_row = summary_table[summary_table["country"] == c_code].iloc[0]
    c_mfg_cagr = c_row[mfg_cagr_col]
    ind_delta_val = ind_share_changes.get(c_code, float('nan'))
    
    # Determine logic (Relative vs. Absolute De-industrialization)
    if pd.notna(c_mfg_cagr):
        de_ind_type = "Absolute" if c_mfg_cagr < 0 else "Relative"
    else:
        de_ind_type = "Unclear"

    mfg_delta_str = f"{mfg_delta_val:.4%}"
    ind_delta_str = f"{ind_delta_val:.4%}" if pd.notna(ind_delta_val) else "NaN"
    c_mfg_cagr_str = f"{c_mfg_cagr:.4%}" if pd.notna(c_mfg_cagr) else "NaN"

    print(
        f"   - {c_code}: Industry Share Change: {ind_delta_str} | "
        f"Manufacturing Share Change: {mfg_delta_str} | "
        f"Manufacturing CAGR: {c_mfg_cagr_str} | Type: {de_ind_type}"
    )


# Q2: Is manufacturing declining faster than total industry?
# Methodology: Compare industry and manufacturing CAGRs globally and specifically within the de-industrializing group

# Global averages
avg_ind_cagr = summary_table[ind_cagr_col].mean()
avg_mfg_cagr = summary_table[mfg_cagr_col].mean()

# De-industrializing countries (identified in Q1)
de_ind_df = summary_table[summary_table["country"].isin(de_ind_countries.index)]
de_ind_avg_ind_cagr = de_ind_df[ind_cagr_col].mean()
de_ind_avg_mfg_cagr = de_ind_df[mfg_cagr_col].mean()

print("\n2. Is manufacturing declining faster than total industry?")
print(f"   - [Global Averages]             Industry CAGR: {avg_ind_cagr:.4%} | Manufacturing CAGR: {avg_mfg_cagr:.4%}")
print(f"   - [De-industrializing Group]   Industry CAGR: {de_ind_avg_ind_cagr:.4%} | Manufacturing CAGR: {de_ind_avg_mfg_cagr:.4%}")


# Q3: Are trends different between advanced and emerging economies?
# Methodology: Compare average CAGR between advanced and emerging countries

advanced_economies = ["AUS", "BEL", "CAN", "DEU", "DNK", "FIN", "FRA", "GBR", "ITA", "JPN", "USA"]
emerging_economies = ["BRA", "CHN", "MEX", "TUR", "ZAF"]

adv_df = summary_table[summary_table["country"].isin(advanced_economies)]
eme_df = summary_table[summary_table["country"].isin(emerging_economies)]

print("\n3. Macro Grouped Trends (Averages):")
print(f"   - Advanced Economies: GDP CAGR: {adv_df[gdp_cagr_col].mean():.4%} | Industry CAGR: {adv_df[ind_cagr_col].mean():.4%} | Manufacturing CAGR: {adv_df[mfg_cagr_col].mean():.4%}")
print(f"   - Emerging Economies: GDP CAGR: {eme_df[gdp_cagr_col].mean():.4%} | Industry CAGR: {eme_df[ind_cagr_col].mean():.4%} | Manufacturing CAGR: {eme_df[mfg_cagr_col].mean():.4%}")