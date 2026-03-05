# ml/scripts/household_data_merger.py
# Cleans Dataset 1 & 2 and merges them into one clean training file

import pandas as pd
import numpy as np
import os

print("=" * 50)
print("HOUSEHOLD DATA MERGER")
print("=" * 50)

# ── Load both datasets ──────────────────────────────
print("\n📂 Loading datasets...")
d1 = pd.read_csv("data/raw/household_filtered.csv")
d2 = pd.read_csv("data/raw/household_gas_data.csv")

print(f"   Dataset 1 rows: {len(d1)}")
print(f"   Dataset 2 rows: {len(d2)}")

# ── Clean Dataset 1 ─────────────────────────────────
print("\n🔧 Cleaning Dataset 1...")

# Strip spaces from column names
d1.columns = d1.columns.str.strip()

# Encode weather_influence: None=0, Low=1, Medium=2, High=3
weather_map = {"None": 0, "Low": 1, "Medium": 2, "High": 3}
d1["weather_influence_encoded"] = d1["weather_influence"].map(weather_map)

# Encode area_type: Urban=0, Semi-urban=1, Rural=2
area_map = {"Urban": 0, "Semi-urban": 1, "Rural": 2}
d1["area_type_encoded"] = d1["area_type"].map(area_map)

print("   ✅ Dataset 1 cleaned")

# ── Clean Dataset 2 ─────────────────────────────────
print("\n🔧 Cleaning Dataset 2...")

# Fix Cylinder_Size: replace 'Not sure' with value from Dataset 1
not_sure_mask = d2["Cylinder_Size"] == "Not sure"
print(f"   Found {not_sure_mask.sum()} 'Not sure' cylinder sizes — fixing...")
d2.loc[not_sure_mask, "Cylinder_Size"] = d1.loc[not_sure_mask, "cylinder_size"].astype(str) + "kg"

# Clean cylinder size: remove 'kg' and convert to float
d2["cylinder_size_kg"] = d2["Cylinder_Size"].str.replace("kg", "").str.strip().astype(float)

# Fix Daily_Gas_Usage_Hours: map categories to numbers
hours_map = {"<1": 0.5, "2": 2.0, "4": 4.0, ">4": 5.0}
d2["daily_hours_num"] = d2["Daily_Gas_Usage_Hours"].map(hours_map)

# Fix Household_Size: map 5+ to 6
size_map = {"1": 1, "2": 2, "3": 3, "4": 4, "5+": 6}
d2["household_size_num"] = d2["Household_Size"].map(size_map)

# Encode Cooking_Frequency
cook_map = {"Once": 1, "Twice": 2, "Three times": 3, "More than three": 4}
d2["cooking_freq_encoded"] = d2["Cooking_Frequency"].map(cook_map)

# Encode Residence_Type
res_map = {"Single house": 0, "Apartment": 1, "Shared housing": 2}
d2["residence_type_encoded"] = d2["Residence_Type"].map(res_map)

# Encode Primary_Gas_Usage
usage_map = {
    "Breakfast only": 0,
    "Lunch & dinner": 1,
    "Full-day cooking": 2,
    "Water heating": 3,
    "Home business": 4
}
d2["primary_usage_encoded"] = d2["Primary_Gas_Usage"].map(usage_map)

# Encode Weather_Impact_Type
weather_type_map = {"No change": 0, "Rainy days": 1, "Cold days": 2}
d2["weather_impact_encoded"] = d2["Weather_Impact_Type"].map(weather_type_map)

# Encode Guest_Impact
guest_map = {"Never": 0, "Rarely": 1, "Sometimes": 2, "Very often": 3}
d2["guest_impact_encoded"] = d2["Guest_Impact"].map(guest_map)

# Parse Cylinder_Install_Date to days since install
d2["Cylinder_Install_Date"] = pd.to_datetime(d2["Cylinder_Install_Date"], errors="coerce")
d2["days_since_install"] = (pd.Timestamp.today() - d2["Cylinder_Install_Date"]).dt.days

print("   ✅ Dataset 2 cleaned")

# ── Build merged dataset ─────────────────────────────
print("\n🔗 Merging datasets...")

merged = pd.DataFrame({
    "user_id":                  d1["User"],
    "area_type":                d1["area_type_encoded"],
    "num_people":               d1["num_people"],
    "avg_daily_hours":          d1["avg_daily_hours"],
    "cylinder_size_kg":         d1["cylinder_size"],
    "weather_influence":        d1["weather_influence_encoded"],
    "usual_duration_days":      d1["usual_duration"],   # TARGET variable
    "residence_type":           d2["residence_type_encoded"],
    "cooking_frequency":        d2["cooking_freq_encoded"],
    "primary_usage":            d2["primary_usage_encoded"],
    "weather_impact_type":      d2["weather_impact_encoded"],
    "guest_impact":             d2["guest_impact_encoded"],
    "days_since_install":       d2["days_since_install"],
})

# Drop rows with any missing values
before = len(merged)
merged = merged.dropna()
after = len(merged)
print(f"   Dropped {before - after} rows with missing values")
print(f"   Final dataset: {after} rows, {len(merged.columns)} columns")

# ── Save ─────────────────────────────────────────────
os.makedirs("data/processed", exist_ok=True)
output_path = "data/processed/household_merged_clean.csv"
merged.to_csv(output_path, index=False)

print(f"\n✅ Saved to {output_path}")
print("\nColumn summary:")
print(merged.describe())
print("\n🎉 Household data merger complete!")