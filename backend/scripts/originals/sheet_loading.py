#!/usr/bin/env python3
import json
import time
from typing import List, Tuple

# --- Selenium imports for browser automation ---
from selenium import webdriver
from selenium.webdriver.common.by import By                 # how we locate elements (By.ID, By.CSS_SELECTOR, etc.)
from selenium.webdriver.common.keys import Keys             # for sending keyboard keys (Enter, etc.)
from selenium.webdriver.support.ui import WebDriverWait     # explicit waits
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)

# --- Driver manager so you don't manually download chromedriver ---
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ------------------- CONFIG PROD -------------------
# ✅ URL of the Django Admin login page (the page where we type username & password)
LOGIN_URL  = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/login/"

# ✅ URL of the Django Admin "Add" form for Content Loading (the page where we paste JSON and click Save)
TARGET_URL = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/nkb_load_data/contentloading/add/"

# ⚠️ Credentials used to log into the Admin site (typed into the login form online)
#    Consider moving these to environment variables or a secrets manager.
USERNAME = "content_loader"
PASSWORD = "C"

# ✅ Public/accessible Google Sheet URL that the script opens in a browser
#    The script *reads live data* from this page: spreadsheet title + sheet tab names.
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1qF_z_uFJojvPHwI9b-o8_d5k-Yr7Moj95L6DRnYOVmQ/edit?gid=1613205683#gid=1613205683"

# (Optional) If you need to stay logged into Google, reuse a Chrome profile.
# Set these to your local Chrome profile paths if desired.
USER_DATA_DIR = None     # e.g. "/home/you/.config/google-chrome"
USER_PROFILE_DIR = None  # e.g. "Default" or "Profile 1"
# ------------------------------------------------

# Google Sheets adds this to the page <title>, we trim it later to get a clean spreadsheet name.
SHEET_TITLE_SUFFIX = " - Google Sheets"


def make_driver(headless: bool = False) -> webdriver.Chrome:
    """
    Create and return a Chrome WebDriver.

    - headless=True runs Chrome without a UI (useful for servers/CI)
    - webdriver_manager auto-downloads a compatible ChromeDriver
    - Optional profile reuse helps stay logged into Google (to open restricted sheets)
    """
    options = webdriver.ChromeOptions()

    # Run headless if requested (Chrome's new headless mode)
    if headless:
        options.add_argument("--headless=new")

    # Common stability/perf flags
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Reuse a Chrome user profile (optional, helpful for Google login)
    if USER_DATA_DIR:
        options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    if USER_PROFILE_DIR:
        options.add_argument(f"--profile-directory={USER_PROFILE_DIR}")

    # Spin up the driver with an auto-managed chromedriver binary
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def get_sheets_info_via_selenium(driver, sheet_url: str, timeout: int = 40) -> Tuple[str, List[str]]:
    """
    OPEN A LIVE GOOGLE SHEETS PAGE (ONLINE READ):

    - Navigates to the Google Sheet URL in a real browser
    - Waits for the page title to indicate Google Sheets has loaded
    - Extracts:
        1) Spreadsheet title (from <title> tag)
        2) Tab (sheet) names (from elements on the page)
    - Returns (spreadsheet_title, [list_of_tab_names])

    If the sheet is private, you must be logged in (use profile reuse).
    """
    driver.get(sheet_url)
    wait = WebDriverWait(driver, timeout)

    # Wait until the window title contains "Google Sheets" → page likely loaded
    try:
        wait.until(EC.title_contains("Google Sheets"))
    except TimeoutException:
        # Not fatal: sometimes the title condition is flaky; continue anyway
        pass

    # Try multiple selectors since Google can change markup:
    # We search for DOM nodes that typically contain the sheet tab labels.
    tab_names: List[str] = []
    for by, sel in [
        (By.CSS_SELECTOR, ".docs-sheet-tab .docs-sheet-tab-name"),
        (By.CSS_SELECTOR, "[role='tab'] .docs-sheet-tab-name"),
        (By.CSS_SELECTOR, "[role='tab'][aria-label]"),
    ]:
        try:
            # Wait for any matching elements to exist in the DOM
            elems = wait.until(EC.presence_of_all_elements_located((by, sel)))
            names = []
            for e in elems:
                # Prefer visible text
                txt = e.text.strip()
                if not txt:
                    # Fallback: some tabs expose name via aria-label (e.g., "Sheet1, selected")
                    aria = e.get_attribute("aria-label") or ""
                    txt = aria.split(",")[0].strip()  # take text before comma
                if txt:
                    names.append(txt)
            if names:
                tab_names = names
                break  # stop at the first selector that produced results
        except TimeoutException:
            continue  # try next selector

    # Derive spreadsheet title from the browser tab title
    title = (driver.title or "").strip()
    if title.endswith(SHEET_TITLE_SUFFIX):
        title = title[: -len(SHEET_TITLE_SUFFIX)].strip()
    if not title:
        title = "Untitled spreadsheet"  # fallback if title missing

    if not tab_names:
        # If you see this, sheet may be restricted or markup changed.
        raise RuntimeError(
            "Couldn't read sheet tab names. If the sheet is restricted, log into Google in this Chrome window and refresh."
        )

    # ➜ RETURNS live ONLINE data we just read from the Google Sheet page
    return title, tab_names


def build_sheet_payload(spreadsheet_name: str, sheet_names: List[str]) -> str:
    """
    Build the JSON payload (a compact JSON string) that will be pasted into the Django Admin form.

    Structure:
    {
      "spread_sheet_name": "<spreadsheet title>",
      "data_sets_to_be_loaded": ["Tab1", "Tab2", ...]
    }
    """
    payload = {
        "spread_sheet_name": spreadsheet_name,
        "data_sets_to_be_loaded": sheet_names,
    }
    # separators=(",", ":") compacts JSON; ensure_ascii=False keeps Unicode intact
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def flexible_login(driver, username: str, password: str, timeout: int = 30):
    """
    ONLINE FORM FILL: LOG INTO DJANGO ADMIN

    Steps:
    1) Open LOGIN_URL
    2) Find username and password inputs (by IDs)
    3) Type USERNAME and PASSWORD (these are your configured strings above)
    4) Submit (Enter or click submit)
    5) Consider login successful if:
        - URL changes, or
        - a logout link appears, or
        - we land on an admin page with 'Admin'/'Dashboard' title, or
        - a form is present.
    """
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, timeout)

    # Locate the username/password inputs
    user_el = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
    pass_el = wait.until(EC.presence_of_element_located((By.ID, "id_password")))

    # Type credentials (this is where your USERNAME/PASSWORD are sent to the online form)
    user_el.clear(); user_el.send_keys(username)
    pass_el.clear(); pass_el.send_keys(password)

    # Press Enter to submit the login form
    pass_el.send_keys(Keys.ENTER)

    # Fallback: if Enter didn't submit, try clicking a submit button
    try:
        WebDriverWait(driver, 1.5).until(
            EC.any_of(
                EC.url_changes(LOGIN_URL),
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='logout']"))
            )
        )
    except TimeoutException:
        try:
            submit = driver.find_element(By.CSS_SELECTOR, "input[type='submit'],button[type='submit']")
            submit.click()
        except NoSuchElementException:
            pass

    # Consider it a success if any of these indicators are found
    try:
        wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='logout']")),
                EC.url_contains("/admin/"),
                EC.title_contains("Admin"),
                EC.title_contains("Dashboard"),
            )
        )
    except TimeoutException:
        # Last resort: at least ensure a form is present
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form")))
        except TimeoutException:
            raise RuntimeError("Login may have failed; run with a visible window and check the page.")


def open_add_form(driver, timeout: int = 10):
    """
    ONLINE NAVIGATION: OPEN THE 'ADD CONTENT LOADING' FORM

    - Goes straight to the add form URL.
    - Waits until a <form> exists on the page.
    """
    driver.get(TARGET_URL)
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form")))


def find_payload_textarea(wait: WebDriverWait):
    """
    Find the textarea where we need to paste the JSON payload.

    Tries several common IDs/Names/XPaths to be robust against small admin UI changes.
    Returns the WebElement if found, else None.
    """
    for by, sel in [
        (By.ID, "id_payload"),
        (By.NAME, "payload"),
        (By.ID, "id_data"),
        (By.NAME, "data"),
        (By.ID, "id_request_body"),
        (By.NAME, "request_body"),
        (By.XPATH, "//form//textarea"),  # very generic fallback
    ]:
        try:
            return wait.until(EC.presence_of_element_located((by, sel)))
        except TimeoutException:
            continue
    return None


def scroll_into_view(driver, element):
    """
    Helper to scroll an element into the middle of the viewport (useful before clicking).
    """
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
        element
    )


def fast_fill_textarea(driver, payload_json: str, timeout: int = 0):
    """
    ONLINE FORM FILL: PASTE JSON PAYLOAD INTO TEXTAREA

    Instead of slow .send_keys typing, inject the value via JavaScript:
      - Set el.value
      - Dispatch 'input' and 'change' events so frameworks detect the update

    This is where the script *writes* the JSON (built from Google Sheets data) into the admin form online.
    """
    wait = WebDriverWait(driver, timeout)
    textarea = find_payload_textarea(wait)

    if not textarea:
        raise RuntimeError("Could not find the Input data textarea.")

    # Directly set the field's value and fire events
    driver.execute_script(
        """
        const el = arguments[0];
        const value = arguments[1];
        el.value = value;                            // set the textarea value
        el.dispatchEvent(new Event('input', {bubbles:true}));   // notify any listeners
        el.dispatchEvent(new Event('change', {bubbles:true}));  // notify any listeners
        """,
        textarea, payload_json
    )


def robust_save_and_view(driver, timeout: int = 10):
    """
    ONLINE ACTION: CLICK 'SAVE AND VIEW' (or fallback to 'Save')

    - Scrolls to bottom to reveal action buttons
    - Tries multiple XPath patterns to find a clickable Save/Save and view button
    - If normal click fails because of overlays, try JS-based click()
    """
    wait = WebDriverWait(driver, timeout)

    # Many admin pages place actions at the bottom; scroll there.
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Try a list of possible button locators to be resilient to UI variations
    xpaths = [
        "//button[normalize-space(.)='Save and view']",
        "//input[@type='submit' and @value='Save and view']",
        "//button[contains(.,'Save and view')]",
        "//input[@type='submit' and contains(@value,'Save and view')]",
        # Fallbacks:
        "//button[@name='_saveandview']",
        "//input[@name='_saveandview']",
        "//button[normalize-space(.)='Save']",
        "//input[@type='submit' and @value='Save']",
    ]

    for xp in xpaths:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            scroll_into_view(driver, btn)
            try:
                btn.click()  # normal click
            except (ElementClickInterceptedException, ElementNotInteractableException):
                # If something blocks the click, try JS click
                driver.execute_script("arguments[0].click();", btn)
            return  # success
        except TimeoutException:
            continue

    raise RuntimeError("Save and view button not found.")


def run(headless: bool = False):
    """
    MAIN ORCHESTRATION:

    Phase 1 (READ ONLINE):
      - Open Google Sheets
      - Read spreadsheet title + sheet tab names
      - Build JSON payload

    Phase 2 (WRITE ONLINE):
      - New browser session
      - Log into Django Admin (types USERNAME/PASSWORD)
      - Open the 'Add Content Loading' form
      - Paste JSON payload into textarea
      - Click 'Save and view'
    """
    # -------- Phase 1: open sheet, read title + tabs (short-lived browser) --------
    driver_sheet = make_driver(headless=headless)
    try:
        # ➜ ONLINE READ from Google Sheets page
        spreadsheet_name, sheet_tabs = get_sheets_info_via_selenium(driver_sheet, GOOGLE_SHEET_URL)
        print("📄 Spreadsheet:", spreadsheet_name)
        print("🗂️ Tabs:", sheet_tabs)

        # Build the JSON we will submit to the admin form
        payload = build_sheet_payload(spreadsheet_name, sheet_tabs)
        print("🧩 Payload to submit:", payload)
    finally:
        # Cleanly close the first browser (the Google Sheets reader)
        try:
            time.sleep(0.5)
            driver_sheet.quit()
        except Exception:
            pass

    # -------- Phase 2: fresh browser for admin form (no dropdown interactions) --------
    driver = make_driver(headless=headless)
    try:
        # ➜ ONLINE FORM FILL: LOGIN (types username/password)
        flexible_login(driver, USERNAME, PASSWORD)

        # ➜ ONLINE NAVIGATION: open the specific "Add" form
        open_add_form(driver)

        # ➜ ONLINE FORM FILL: paste the payload JSON into the textarea
        fast_fill_textarea(driver, payload)

        # ➜ ONLINE ACTION: click "Save and view" (or "Save")
        robust_save_and_view(driver)

        # At this point, the form submission should be done.
        print("✅ Done! Submitted and saved successfully.")
        print("🔗 Final URL:", driver.current_url)
    finally:
        # Leave the window open for 2s (useful if not headless) so you can see the result
        time.sleep(2)
        # NOTE: driver.quit() is commented out intentionally to keep the window open after script ends.
        # driver.quit()


if __name__ == "__main__":
    # Set headless=False to watch the browser; set True for servers/automation.
    run(headless=False)

