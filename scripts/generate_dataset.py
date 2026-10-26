"""
Generates data/Housing.csv: a synthetic dataset that mirrors the structure,
column names and statistical shape of the Kaggle "Housing Prices Dataset"
(uploaded by Yasser H.) referenced in the capstone spec -- 545 rows with
price, area, bedrooms, bathrooms, stories, mainroad, guestroom, basement,
hotwaterheating, airconditioning, parking, prefarea and furnishingstatus.

Run once:  python scripts/generate_dataset.py
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 545


def yes_no(p_yes, n=N):
    return np.where(RNG.random(n) < p_yes, "yes", "no")


def main():
    area = np.round(RNG.lognormal(mean=8.45, sigma=0.32, size=N))
    area = np.clip(area, 1650, 16200).astype(int)

    bedrooms = RNG.choice([1, 2, 3, 4, 5, 6], size=N, p=[0.02, 0.18, 0.44, 0.27, 0.07, 0.02])
    bathrooms = RNG.choice([1, 2, 3, 4], size=N, p=[0.62, 0.30, 0.06, 0.02])
    stories = RNG.choice([1, 2, 3, 4], size=N, p=[0.38, 0.34, 0.20, 0.08])
    parking = RNG.choice([0, 1, 2, 3], size=N, p=[0.35, 0.32, 0.25, 0.08])

    mainroad = yes_no(0.86)
    guestroom = yes_no(0.18)
    basement = yes_no(0.35)
    hotwaterheating = yes_no(0.05)
    airconditioning = yes_no(0.32)
    prefarea = yes_no(0.23)
    furnishingstatus = RNG.choice(
        ["furnished", "semi-furnished", "unfurnished"], size=N, p=[0.22, 0.41, 0.37]
    )

    def b(arr):
        return (arr == "yes").astype(int)

    furnishing_bonus = np.select(
        [furnishingstatus == "furnished", furnishingstatus == "semi-furnished"],
        [300_000, 120_000],
        default=0,
    )

    price = (
        1_300_000
        + 320 * area
        + 105_000 * bedrooms
        + 900_000 * bathrooms
        + 420_000 * stories
        + 300_000 * b(mainroad)
        + 280_000 * b(guestroom)
        + 350_000 * b(basement)
        + 650_000 * b(hotwaterheating)
        + 700_000 * b(airconditioning)
        + 280_000 * parking
        + 550_000 * b(prefarea)
        + furnishing_bonus
        + RNG.normal(0, 840_000, size=N)
    )
    price = np.clip(price, 1_750_000, 13_300_000).round(-3).astype(int)

    df = pd.DataFrame(
        {
            "price": price,
            "area": area,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "stories": stories,
            "mainroad": mainroad,
            "guestroom": guestroom,
            "basement": basement,
            "hotwaterheating": hotwaterheating,
            "airconditioning": airconditioning,
            "parking": parking,
            "prefarea": prefarea,
            "furnishingstatus": furnishingstatus,
        }
    ).sort_values("price", ascending=False).reset_index(drop=True)

    df.to_csv("data/Housing.csv", index=False)
    print(f"Wrote data/Housing.csv with {len(df)} rows")
    print(df.describe(include="all").T)


if __name__ == "__main__":
    main()
