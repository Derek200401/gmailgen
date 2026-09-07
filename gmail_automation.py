"""Hydra Gmail Generator automation helpers.

This module keeps the Gmail-related logic reusable so a small web app can fill in
account details from a form while the Selenium flow remains testable.
"""

from __future__ import annotations

import argparse
import logging
import os
import random
import shutil
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from unidecode import unidecode

logger = logging.getLogger(__name__)


def normalize_name(value: str) -> str:
    """Return a lowercase ASCII name suitable for username generation."""
    cleaned = (value or "").strip().lower()
    return unidecode(cleaned).replace(" ", "")


def build_account_payload(
    first_name: str,
    last_name: str,
    username: str = "",
    birthday: str = "",
    gender: str = "male",
    password: str = "P@ssWoRd910.",
) -> dict:
    """Create a dictionary of values the form can use."""
    first_name_value = (first_name or "John").strip() or "John"
    last_name_value = (last_name or "Smith").strip() or "Smith"
    safe_username = (username or "").strip() or f"{normalize_name(first_name_value)}.{normalize_name(last_name_value)}"
    birth_date = birthday.strip() or random_birthday()
    password_value = password.strip() or "P@ssWoRd910."

    return {
        "first_name": first_name_value,
        "last_name": last_name_value,
        "username": safe_username,
        "birthday": birth_date,
        "gender": (gender or "male").lower(),
        "password": password_value,
        "gmail": f"{safe_username}@gmail.com",
    }


def generate_random_account() -> dict:
    """Return a realistic randomized Gmail account payload."""
    first_names = [
        "Aitana", "Alonso", "Amparo", "Beatriz", "Carlos", "Clara", "Daniel", "Elena", "Fabio", "Gabriel",
        "Hugo", "Isabel", "Javier", "Laura", "Mateo", "Nadia", "Olivia", "Pablo", "Raquel", "Sofia"
    ]
    last_names = [
        "Aguilar", "Alvarez", "Castillo", "Diaz", "Fernandez", "Garcia", "Hernandez", "Lopez", "Morales",
        "Navarro", "Ortiz", "Paredes", "Ramirez", "Sanchez", "Torres", "Vargas", "Zamora"
    ]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    username = f"{normalize_name(first_name)}.{normalize_name(last_name)}{random.randint(100, 9999)}"
    return build_account_payload(
        first_name=first_name,
        last_name=last_name,
        username=username,
        birthday=random_birthday(),
        gender=random.choice(["male", "female", "other"]),
        password="P@ssWoRd910.",
    )


def random_birthday(min_age: int = 18, max_age: int = 70) -> str:
    """Generate a realistic birthday in the DD MM YYYY format."""
    today = datetime.today()
    start_date = datetime(today.year - max_age, 1, 1)
    end_date = datetime(today.year - min_age, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    birth_date = start_date + timedelta(days=random_days)
    return f"{birth_date.day} {birth_date.month} {birth_date.year}"


def gender_option_value(gender: str) -> str:
    """Return Google's language-independent value for a gender option."""
    values = {
        "female": "1",
        "male": "2",
        "other": "3",
        "custom": "4",
    }
    return values.get(str(gender).lower(), "3")


def detect_browser_paths():
    """Return the best browser and driver paths from the environment or PATH."""
    browser_candidates = [
        os.environ.get("GOOGLE_CHROME_BIN"),
        os.environ.get("CHROME_BIN"),
        os.environ.get("CHROME_PATH"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("chrome"),
    ]
    browser_binary = next((value for value in browser_candidates if value and os.path.exists(value)), None)

    driver_candidates = [
        os.environ.get("CHROMEDRIVER_PATH"),
        shutil.which("chromedriver"),
        "chromedriver.exe",
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
    ]
    driver_path = next((value for value in driver_candidates if value and (os.path.exists(value) or shutil.which(value))), None)
    return browser_binary, driver_path


def create_driver(headless: bool = True):
    """Create a Chrome webdriver instance with common stability flags."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--window-size=1280,1024")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})

    if headless:
        chrome_options.add_argument("--headless=new")

    browser_binary, driver_path = detect_browser_paths()
    if browser_binary:
        chrome_options.binary_location = browser_binary

    if driver_path:
        service = webdriver.ChromeService(executable_path=driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    try:
        return webdriver.Chrome(options=chrome_options)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Chrome or ChromeDriver is not installed in this runtime. On Railway, install Chromium + chromedriver or set CHROME_BIN and CHROMEDRIVER_PATH."
        ) from exc


def fill_name(driver, wait, first_name: str, last_name: str) -> None:
    first_name_field = wait.until(EC.presence_of_element_located((By.NAME, "firstName")))
    first_name_field.clear()
    first_name_field.send_keys(first_name)

    last_name_field = driver.find_element(By.NAME, "lastName")
    last_name_field.clear()
    last_name_field.send_keys(last_name)

    next_button = driver.find_element(By.CLASS_NAME, "VfPpkd-LgbsSe")
    next_button.click()
    logger.info("Name step completed.")


def fill_birthday_and_gender(driver, wait, birthday: str, gender: str) -> None:
    wait.until(EC.visibility_of_element_located((By.NAME, "day")))
    your_day, your_month, your_year = birthday.split()

    month_div = wait.until(EC.element_to_be_clickable((By.ID, "month")))
    month_div.click()

    month_option = wait.until(EC.element_to_be_clickable((
        By.XPATH, f"//li[@role='option' and @data-value='{int(your_month)}']"
    )))
    month_option.click()

    driver.find_element(By.ID, "day").clear()
    driver.find_element(By.ID, "day").send_keys(your_day)
    driver.find_element(By.ID, "year").clear()
    driver.find_element(By.ID, "year").send_keys(your_year)

    gender_value = gender_option_value(gender)

    gender_div = wait.until(EC.element_to_be_clickable((By.ID, "gender")))
    gender_div.click()

    gender_option = wait.until(EC.element_to_be_clickable((
        By.XPATH, f"//li[@role='option' and @data-value='{gender_value}']"
    )))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", gender_option)
    gender_option.click()

    next_button = driver.find_element(By.CLASS_NAME, "VfPpkd-LgbsSe")
    next_button.click()
    logger.info("Birthday and gender step completed.")


def fill_gmailaddress(driver, wait, username: str) -> None:
    custom_buttons = driver.find_elements(By.XPATH, "//div[contains(text(), 'Crear dirección de Gmail personalizada')]")
    if custom_buttons:
        custom_buttons[0].click()

    if driver.find_elements(By.CLASS_NAME, "uxXgMe"):
        create_own_option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[jsname='CeL6Qc']")))
        create_own_option.click()

    username_field = wait.until(EC.element_to_be_clickable((By.NAME, "Username")))
    username_field.clear()
    username_field.send_keys(username)
    driver.find_element(By.CLASS_NAME, "VfPpkd-LgbsSe").click()
    logger.info("Gmail address step completed.")


def fill_password(driver, wait, password: str) -> None:
    password_field = wait.until(EC.visibility_of_element_located((By.NAME, "Passwd")))
    password_field.clear()
    password_field.send_keys(password)

    confirm_field = driver.find_element(By.ID, "confirm-passwd").find_element(By.NAME, "PasswdAgain")
    confirm_field.clear()
    confirm_field.send_keys(password)

    driver.find_element(By.CLASS_NAME, "VfPpkd-LgbsSe").click()
    logger.info("Password step completed.")


def run_gmail_creation(account: dict, headless: bool = True):
    """Create a Gmail account for the supplied account payload."""
    driver = create_driver(headless=headless)
    try:
        driver.get("https://accounts.google.com/signup/v2/createaccount?flowName=GlifWebSignIn&flowEntry=SignUp")
        wait = WebDriverWait(driver, 20)

        fill_name(driver, wait, account["first_name"], account["last_name"])
        fill_birthday_and_gender(driver, wait, account["birthday"], account["gender"])
        time.sleep(2)
        fill_gmailaddress(driver, wait, account["username"])
        fill_password(driver, wait, account["password"])
        time.sleep(2)

        if driver.find_elements(By.ID, "phoneNumberId"):
            wait.until(EC.element_to_be_clickable((By.ID, "phoneNumberId")))
            phone_field = driver.find_element(By.ID, "phoneNumberId")
            phone_field.clear()
            phone_field.send_keys("+2126" + str(random.randint(10000000, 99999999)))
            driver.find_element(By.CLASS_NAME, "VfPpkd-vQzf8d").click()
            time.sleep(2)

            while driver.find_elements(By.CLASS_NAME, "AfGCob"):
                phone_field.clear()
                phone_field.send_keys("+2126" + str(random.randint(10000000, 99999999)))
                try:
                    driver.find_element(By.CLASS_NAME, "VfPpkd-vQzf8d").click()
                except Exception:
                    break
                time.sleep(2)
        else:
            skip_buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button span.VfPpkd-vQzf8d")))
            for button in skip_buttons:
                button.click()

        try:
            agree_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button span.VfPpkd-vQzf8d")))
            agree_button.click()
        except Exception:
            logger.warning("Terms confirmation button was not available; flow may have reached a different step.")

        logger.info("Gmail account creation flow completed for %s", account["gmail"])
        return {
            "status": "success",
            "gmail": account["gmail"],
            "password": account["password"],
        }
    except Exception as exc:  # pragma: no cover - Selenium browser actions are environment-specific
        logger.exception("Gmail creation failed")
        if isinstance(exc, FileNotFoundError):
            return {
                "status": "error",
                "message": "Chrome/ChromeDriver is not installed in this environment. Deploy with Chromium and chromedriver enabled, or run locally on a machine with a Chrome browser installed.",
            }
        return {"status": "error", "message": str(exc)}
    finally:
        if 'driver' in locals():
            driver.quit()


def parse_args():
    parser = argparse.ArgumentParser(description="Hydra Gmail Generator")
    parser.add_argument("--first-name", default="Aitana")
    parser.add_argument("--last-name", default="Garcia")
    parser.add_argument("--username", default="")
    parser.add_argument("--birthday", default="")
    parser.add_argument("--gender", default="female")
    parser.add_argument("--password", default="P@ssWoRd910.")
    return parser.parse_args()


def main():
    """Generate a Gmail account using a direct script invocation or default values."""
    args = parse_args()
    payload = build_account_payload(
        first_name=args.first_name,
        last_name=args.last_name,
        username=args.username,
        birthday=args.birthday or random_birthday(),
        gender=args.gender,
        password=args.password,
    )
    result = run_gmail_creation(payload, headless=True)
    print(result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()

#     "Sophie", "Stéphane", "Suzanne", "Théo", "Thomas", "Valentin", "Valérie", "Victor", "Vincent", "Yves",
#     "Zoé", "Adèle", "Adrien", "Alexandre", "Alice", "Alix", "Anatole", "André", "Angèle", "Anne",
#     "Baptiste", "Basile", "Bernard", "Brigitte", "Céleste", "Céline", "Christophe", "Cyril", "Denis", "Diane",
#     "Édouard", "Éléonore", "Émile", "Félix", "Florence", "Georges", "Gérard", "Guillaume", "Hugo", "Inès",
#     "Jacques", "Jean", "Jeanne", "Joséphine", "Julien", "Laure", "Lucie", "Maëlle", "Marcel", "Martine",
#     "Maxime", "Michel", "Nina", "Océane", "Paul", "Perrine", "Quentin", "Romain", "Solène", "Thérèse"
# ]
# last_names = [
#     "Leroy", "Moreau", "Bernard", "Dubois", "Durand", "Lefebvre", "Mercier", "Dupont", "Fournier", "Lambert",
#     "Fontaine", "Rousseau", "Vincent", "Muller", "Lefèvre", "Faure", "André", "Gauthier", "Garcia", "Perrin",
#     "Robin", "Clement", "Morin", "Nicolas", "Henry", "Roussel", "Mathieu", "Garnier", "Chevalier", "François",
#     "Legrand", "Gérard", "Boyer", "Gautier", "Roche", "Roy", "Noel", "Meyer", "Lucas", "Gomez",
#     "Martinez", "Caron", "Da Silva", "Lemoine", "Philippe", "Bourgeois", "Pierre", "Renard", "Girard", "Brun",
#     "Gaillard", "Barbier", "Arnaud", "Martins", "Rodriguez", "Picard", "Roger", "Schmitt", "Colin", "Vidal",
#     "Dupuis", "Pires", "Renaud", "Renault", "Klein", "Coulon", "Grondin", "Leclerc", "Pires", "Marchand",
#     "Dufour", "Blanchard", "Gillet", "Chevallier", "Fernandez", "David", "Bouquet", "Gilles", "Fischer", "Roy",
#     "Besson", "Lemoine", "Delorme", "Carpentier", "Dumas", "Marin", "Gosselin", "Mallet", "Blondel", "Adam",
#     "Durant", "Laporte", "Boutin", "Lacombe", "Navarro", "Langlois", "Deschamps", "Schneider", "Pasquier", "Renaud"
# ]