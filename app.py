"""
House Price Prediction -- Flask web application (KZ-ML-01).

Loads the trained model (model/model.pkl) and its feature-column order
(model/columns.pkl), serves a prediction form, and logs every prediction to
a SQLite database (predictions.db) for the history page.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "predictions.db"
MODEL_PATH = BASE_DIR / "model" / "model.pkl"
COLUMNS_PATH = BASE_DIR / "model" / "columns.pkl"
METRICS_PATH = BASE_DIR / "model" / "metrics.json"

BINARY_FIELDS = [
    "mainroad", "guestroom", "basement",
    "hotwaterheating", "airconditioning", "prefarea",
]
FURNISHING_OPTIONS = ["furnished", "semi-furnished", "unfurnished"]
FIELD_LABELS = {
    "area": "Area",
    "bedrooms": "Bedrooms",
    "bathrooms": "Bathrooms",
    "stories": "Stories",
    "parking": "Parking spaces",
    "mainroad": "Main road access",
    "guestroom": "Guest room",
    "basement": "Basement",
    "hotwaterheating": "Hot water heating",
    "airconditioning": "Air conditioning",
    "prefarea": "Preferred area",
    "furnishingstatus": "Furnishing status",
}

app = Flask(__name__)
app.secret_key = "kz-ml-01-dev-secret"

model = joblib.load(MODEL_PATH)
feature_columns = joblib.load(COLUMNS_PATH)
metrics = json.loads(METRICS_PATH.read_text()) if METRICS_PATH.exists() else {}

app.jinja_env.filters["inr"] = lambda amount: format_inr(amount)


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area INTEGER NOT NULL,
            bedrooms INTEGER NOT NULL,
            bathrooms INTEGER NOT NULL,
            stories INTEGER NOT NULL,
            parking INTEGER NOT NULL,
            other_features TEXT NOT NULL,
            predicted_price REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.commit()
    db.close()


def format_inr(amount):
    amount = int(round(amount))
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))
    if len(digits) > 3:
        last3 = digits[-3:]
        rest = digits[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        digits = ",".join(groups) + "," + last3
    return f"{sign}₹{digits}"


def format_inr_words(amount):
    amount = abs(amount)
    if amount >= 1_00_00_000:
        return f"≈ {amount / 1_00_00_000:.2f} Cr"
    if amount >= 1_00_000:
        return f"≈ {amount / 1_00_000:.2f} Lakh"
    return f"≈ {amount:,.0f}"


def parse_int_field(form, field, min_value, errors, required=True):
    label = FIELD_LABELS[field]
    raw = (form.get(field) or "").strip()
    if raw == "":
        if required:
            errors.append(f"{label} is required.")
        return None
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"{label} must be a whole number.")
        return None
    if value < min_value:
        if min_value > 0:
            errors.append(f"{label} must be a positive number greater than 0.")
        else:
            errors.append(f"{label} cannot be negative.")
        return None
    return value


def parse_and_validate(form):
    errors = []
    data = {
        "area": parse_int_field(form, "area", min_value=1, errors=errors),
        "bedrooms": parse_int_field(form, "bedrooms", min_value=1, errors=errors),
        "bathrooms": parse_int_field(form, "bathrooms", min_value=1, errors=errors),
        "stories": parse_int_field(form, "stories", min_value=1, errors=errors),
        "parking": parse_int_field(form, "parking", min_value=0, errors=errors),
    }

    if data["area"] is not None and data["area"] > 200_000:
        errors.append("Area looks unrealistically large -- please check the value.")

    for field in BINARY_FIELDS:
        data[field] = "yes" if form.get(field) == "on" else "no"

    furnishing = form.get("furnishingstatus", "")
    if furnishing not in FURNISHING_OPTIONS:
        errors.append("Please select a valid furnishing status.")
    data["furnishingstatus"] = furnishing

    return data, errors


def build_feature_vector(data):
    row = {
        "area": data["area"],
        "bedrooms": data["bedrooms"],
        "bathrooms": data["bathrooms"],
        "stories": data["stories"],
        "mainroad": 1 if data["mainroad"] == "yes" else 0,
        "guestroom": 1 if data["guestroom"] == "yes" else 0,
        "basement": 1 if data["basement"] == "yes" else 0,
        "hotwaterheating": 1 if data["hotwaterheating"] == "yes" else 0,
        "airconditioning": 1 if data["airconditioning"] == "yes" else 0,
        "parking": data["parking"],
        "prefarea": 1 if data["prefarea"] == "yes" else 0,
        "furnishingstatus_semi-furnished": 1 if data["furnishingstatus"] == "semi-furnished" else 0,
        "furnishingstatus_unfurnished": 1 if data["furnishingstatus"] == "unfurnished" else 0,
    }
    frame = pd.DataFrame([row]).reindex(columns=feature_columns, fill_value=0)
    return frame


@app.route("/")
def index():
    return render_template("index.html", furnishing_options=FURNISHING_OPTIONS, form_data={})


@app.route("/predict", methods=["POST"])
def predict():
    data, errors = parse_and_validate(request.form)
    if errors:
        for error in errors:
            flash(error, "error")
        return render_template(
            "index.html",
            furnishing_options=FURNISHING_OPTIONS,
            form_data=request.form,
        ), 400

    features = build_feature_vector(data)
    prediction = max(float(model.predict(features)[0]), 0.0)

    other_features = {field: data[field] for field in BINARY_FIELDS}
    other_features["furnishingstatus"] = data["furnishingstatus"]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    db.execute(
        """INSERT INTO predictions
           (area, bedrooms, bathrooms, stories, parking, other_features, predicted_price, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["area"], data["bedrooms"], data["bathrooms"], data["stories"], data["parking"],
            json.dumps(other_features), prediction, created_at,
        ),
    )
    db.commit()
    db.close()

    return render_template(
        "result.html",
        price_inr=format_inr(prediction),
        price_words=format_inr_words(prediction),
        price_raw=round(prediction, 2),
        data=data,
        other_features=other_features,
    )


@app.route("/history")
def history():
    db = get_db()
    rows = db.execute("SELECT * FROM predictions ORDER BY id DESC").fetchall()
    db.close()

    records = []
    for row in rows:
        record = dict(row)
        record["other_features"] = json.loads(row["other_features"])
        record["price_inr"] = format_inr(row["predicted_price"])
        records.append(record)

    return render_template("history.html", records=records)


@app.route("/history/clear", methods=["POST"])
def clear_history():
    db = get_db()
    db.execute("DELETE FROM predictions")
    db.commit()
    db.close()
    flash("Prediction history cleared.", "success")
    return redirect(url_for("history"))


@app.route("/insights")
def insights():
    return render_template("insights.html", metrics=metrics)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
