# ml/scripts/synthetic_station_data_generator.py
# Generates realistic 365-day station sales data from survey statistics

import pandas as pd
import numpy as np
import os

print("=" * 50)
print("SYNTHETIC STATION DATA GENERATOR")
print("=" * 50)

# Set random seed for reproducibility
np.random.seed(42)

# ── Load survey data ────────────────────────────────
print("\n📂 Loading gas station survey...")
survey = pd.read_csv("data/raw/gas_station_survey.csv")
print(f"   Survey rows: {len(survey)}")

# ── Define 15 station profiles from survey ──────────
# Base volumes come from survey Daily_Cylinder_Sales ranges
stations = [
    # Urban stations (6)
    {"id": "STN_001", "type": "Urban",      "base_vol": 200, "lead_days": 3,  "stockout_prob": 0.02},
    {"id": "STN_002", "type": "Urban",      "base_vol": 350, "lead_days": 2,  "stockout_prob": 0.01},
    {"id": "STN_003", "type": "Urban",      "base_vol": 75,  "lead_days": 5,  "stockout_prob": 0.03},
    {"id": "STN_004", "type": "Urban",      "base_vol": 200, "lead_days": 3,  "stockout_prob": 0.02},
    {"id": "STN_005", "type": "Urban",      "base_vol": 40,  "lead_days": 2,  "stockout_prob": 0.05},
    {"id": "STN_006", "type": "Urban",      "base_vol": 350, "lead_days": 10, "stockout_prob": 0.01},
    # Semi-urban stations (5)
    {"id": "STN_007", "type": "Semi-urban", "base_vol": 200, "lead_days": 5,  "stockout_prob": 0.03},
    {"id": "STN_008", "type": "Semi-urban", "base_vol": 75,  "lead_days": 5,  "stockout_prob": 0.04},
    {"id": "STN_009", "type": "Semi-urban", "base_vol": 350, "lead_days": 10, "stockout_prob": 0.02},
    {"id": "STN_010", "type": "Semi-urban", "base_vol": 40,  "lead_days": 10, "stockout_prob": 0.06},
    {"id": "STN_011", "type": "Semi-urban", "base_vol": 75,  "lead_days": 5,  "stockout_prob": 0.03},
    # Rural stations (4)
    {"id": "STN_012", "type": "Rural",      "base_vol": 40,  "lead_days": 10, "stockout_prob": 0.08},
    {"id": "STN_013", "type": "Rural",      "base_vol": 75,  "lead_days": 10, "stockout_prob": 0.05},
    {"id": "STN_014", "type": "Rural",      "base_vol": 350, "lead_days": 10, "stockout_prob": 0.02},
    {"id": "STN_015", "type": "Rural",      "base_vol": 40,  "lead_days": 10, "stockout_prob": 0.10},
]

# ── Sri Lanka festival dates 2024 ───────────────────
festival_dates = [
    "2024-01-15",  # Thai Pongal
    "2024-02-04",  # Independence Day
    "2024-04-12", "2024-04-13", "2024-04-14",  # Sinhala & Tamil New Year
    "2024-05-23",  # Vesak
    "2024-06-21",  # Poson
    "2024-10-31",  # Deepavali
    "2024-12-25",  # Christmas
    "2024-12-31",  # New Year Eve
]
festival_dates = pd.to_datetime(festival_dates)

def get_season(month):
    """Sri Lanka seasons"""
    if month in [5, 6, 7, 8, 9]:
        return "SW_Monsoon"    # May-Sep: rainy
    elif month in [10, 11, 12, 1]:
        return "NE_Monsoon"    # Oct-Jan: rainy
    else:
        return "Dry"           # Feb-Apr: dry

def get_multiplier(date, station_type):
    """Calculate demand multiplier for a given date"""
    multiplier = 1.0

    # Weekend boost
    if date.weekday() >= 5:
        multiplier *= 1.20

    # Festival boost (3 days around festival)
    for fd in festival_dates:
        if abs((date - fd).days) <= 2:
            multiplier *= 1.35
            break

    # Season effect
    season = get_season(date.month)
    if season == "SW_Monsoon":
        multiplier *= 1.15
    elif season == "NE_Monsoon":
        multiplier *= 1.10

    # Urban stations do better on weekdays too
    if station_type == "Urban" and date.weekday() < 5:
        multiplier *= 1.05

    return multiplier

# ── Generate data ───────────────────────────────────
print("\n⚙️  Generating 365 days of data for 15 stations...")

date_range = pd.date_range("2024-01-01", "2024-12-31", freq="D")
all_records = []

for station in stations:
    stock = station["base_vol"] * 7  # Start with 1 week of stock
    week_number = 0

    for i, date in enumerate(date_range):
        if i % 7 == 0:
            week_number += 1

        # Base sales with trend (+0.3% per week)
        trend_factor = 1 + (0.003 * week_number)
        base = station["base_vol"] * trend_factor

        # Apply multipliers
        multiplier = get_multiplier(date, station["type"])
        sales = base * multiplier

        # Add Gaussian noise (±10%)
        noise = np.random.normal(0, sales * 0.10)
        sales = max(0, sales + noise)

        # Simulate stockout
        if np.random.random() < station["stockout_prob"]:
            sales = 0

        sales = int(round(sales))

        # Update rolling stock
        restock = station["base_vol"] * 3 if stock < station["base_vol"] else 0
        stock = max(0, stock - sales + restock)

        # Check if festival week
        is_festival = any(abs((date - fd).days) <= 2 for fd in festival_dates)

        all_records.append({
            "station_id":       station["id"],
            "station_type":     station["type"],
            "date":             date.strftime("%Y-%m-%d"),
            "cylinders_sold":   sales,
            "stock_available":  int(stock),
            "day_of_week":      date.weekday(),
            "is_weekend":       int(date.weekday() >= 5),
            "is_festival_week": int(is_festival),
            "season":           get_season(date.month),
            "supplier_lead_days": station["lead_days"],
            "month":            date.month,
            "week_number":      week_number,
        })

# ── Save ─────────────────────────────────────────────
df = pd.DataFrame(all_records)
output_path = "data/processed/station_sales_synthetic.csv"
df.to_csv(output_path, index=False)

total = len(df)
print(f"\n✅ Generated {total} rows ({total // 15} days × 15 stations)")
print(f"✅ Saved to {output_path}")
print("\nSample data:")
print(df.head(10).to_string())
print(f"\nSales stats per station type:")
print(df.groupby("station_type")["cylinders_sold"].describe().round(1))
print("\n🎉 Synthetic station data generation complete!")