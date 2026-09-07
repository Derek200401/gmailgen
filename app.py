from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request

from gmail_automation import build_account_payload, generate_random_account, run_gmail_creation

app = Flask(__name__)
app.config["TITLE"] = "Hydra Gmail Generator"
app.config["LOGS"] = []
LOG_FILE = Path(__file__).resolve().parent / "hydra_app.log"


def add_log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    app.config["LOGS"].append(entry)
    while len(app.config["LOGS"]) > 50:
        app.config["LOGS"].pop(0)
    logging.info(message)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)


def build_default_form() -> dict:
    return {
        "first_name": "John",
        "last_name": "Smith",
        "username": "john.smith",
        "birthday": "12 5 1990",
        "gender": "male",
        "password": "TestPass!123",
    }


def build_random_form() -> dict:
    account = generate_random_account()
    return {
        "first_name": account["first_name"],
        "last_name": account["last_name"],
        "username": account["username"],
        "birthday": account["birthday"],
        "gender": account["gender"],
        "password": account["password"],
    }


@app.route("/healthz")
def healthz():
    return {"status": "ok", "app": "Hydra Gmail Generator"}, 200


@app.route("/", methods=["GET", "POST"])
def index():
    form = build_default_form()
    result = None

    if request.method == "POST":
        if request.form.get("action") == "randomize":
            form = build_random_form()
            add_log("Generated a randomized account payload for the form.")
        else:
            form = {key: (request.form.get(key) or "").strip() for key in build_default_form()}
            add_log(f"User submitted account form for {form.get('first_name', '')} {form.get('last_name', '')}.")

            if not all(form.values()):
                result = {"status": "error", "message": "Please complete all fields before starting the generator."}
                add_log("Validation failed: required fields were left blank.")
            else:
                payload = build_account_payload(
                    first_name=form["first_name"],
                    last_name=form["last_name"],
                    username=form["username"],
                    birthday=form["birthday"],
                    gender=form["gender"],
                    password=form["password"],
                )
                add_log(f"Starting Gmail automation for {payload['gmail']}.")
                result = run_gmail_creation(payload, headless=True)
                if result.get("status") == "success":
                    add_log(f"Automation completed successfully for {result['gmail']}.")
                else:
                    add_log(f"Automation failed: {result.get('message', 'Unknown error')}")

    return render_template("index.html", form=form, result=result, logs=app.config["LOGS"], title="Hydra Gmail Generator")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
