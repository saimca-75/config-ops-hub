from flask import Flask, request, redirect, url_for, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
import traceback
import time
import os
from typing import Optional
from selenium.webdriver.chrome.options import Options

chrome_opts = Options()
# your existing args...
chrome_opts.add_argument("--disable-extensions")  # ← disables all extensions
# If you also want a clean, temporary profile each run (no cached extensions/cookies):
import tempfile, os
tmp_profile = tempfile.mkdtemp(prefix="selenium_profile_")
chrome_opts.add_argument(f"--user-data-dir={tmp_profile}")


app = Flask(__name__)

# ------------------ HTML TEMPLATES (inline for simplicity) ------------------
FORM_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Django Admin UUID Duration Cleaner</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    form { max-width: 900px; }
    label { display:block; font-weight:600; margin-top: 1rem; }
    input[type=text], input[type=password], textarea { width:100%; padding:10px; border:1px solid #ccc; border-radius:8px; }
    textarea { min-height: 160px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .hint { color:#555; font-size: 0.9rem; margin-top: .3rem; }
    .btn { margin-top: 1.5rem; padding: 12px 18px; border:0; border-radius:8px; background:#0d6efd; color:#fff; cursor:pointer; }
    .btn:disabled { opacity: .7; }
    .small { font-size: .85rem; }
    .note { background:#f6f8fa; padding:10px 12px; border-radius:8px; }
  </style>
</head>
<body>
  <h1>Clear “Duration in sec” for Unit UUIDs</h1>
  <p class="note small">This runs Selenium against your Django Admin. Provide credentials and URLs below.<br>
  <strong>Security note:</strong> Only run locally and never expose this server publicly.</p>

  <form method="post" action="{{ url_for('run_task') }}">
    <label>Login URL</label>
    <input type="text" name="login_url" placeholder="https://.../admin/login/" required value="{{ defaults.get('login_url','') }}">
    <div class="hint small">e.g. https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/login/</div>

    <label>Target Unit List URL</label>
    <input type="text" name="target_url" placeholder="https://.../admin/nkb_resources/unit/" required value="{{ defaults.get('target_url','') }}">
    <div class="hint small">e.g. https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/nkb_resources/unit/</div>

    <div class="row">
      <div>
        <label>Username</label>
        <input type="text" name="username" required value="{{ defaults.get('username','') }}">
      </div>
      <div>
        <label>Password</label>
        <input type="password" name="password" required value="{{ defaults.get('password','') }}">
      </div>
    </div>

    <label>UUIDs (one per line or comma-separated)</label>
    <textarea name="uuids" placeholder="uuid-1&#10;uuid-2&#10;uuid-3" required>{{ defaults.get('uuids','') }}</textarea>

    <div class="row">
      <div>
        <label>Chrome Profile Dir (optional)</label>
        <input type="text" name="profile_dir" placeholder="/path/to/selenium_profile" value="{{ defaults.get('profile_dir','') }}">
        <div class="hint small">Keeps your session (e.g., /home/user/selenium_profile). Leave empty to use a fresh profile.</div>
      </div>
      <div>
        <label>Headless Mode</label>
        <input type="checkbox" name="headless" {{ 'checked' if defaults.get('headless') else '' }}> Run Chrome headless
      </div>
    </div>

    <button class="btn" type="submit">Run</button>
  </form>
</body>
</html>
"""

RESULT_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Run Results</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    pre { background:#0b1020; color:#e7eaf6; padding:16px; border-radius:8px; overflow:auto; }
    a { color:#0d6efd; }
  </style>
</head>
<body>
  <h1>Results</h1>
  <p><a href="{{ url_for('index') }}">← Back</a></p>
  <pre>{{ log }}</pre>
</body>
</html>
"""

# ------------------ SELENIUM CORE (parameterized) ------------------

def make_driver(headless: bool = True, profile_dir: Optional[str] = None) -> webdriver.Chrome:
    opts = Options()
    # Persist profile to keep Django/SSO sessions if desired
    if profile_dir:
        os.makedirs(profile_dir, exist_ok=True)
        opts.add_argument(f"--user-data-dir={profile_dir}")
    # For stability in Linux CI/containers
    opts.add_argument("--window-size=1400,1000")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    if headless:
        opts.add_argument("--headless=new")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def login_if_needed(driver, wait, target_url: str, login_url: str, username: str, password: str, log):
    """Open target; if redirected to login, perform login and return to target."""
    driver.get(target_url)
    time.sleep(1.0)
    cur = driver.current_url
    if "/login" in cur or "/login/" in cur:
        log.append(f"- Redirected to login; performing login at: {login_url}")
        driver.get(login_url)
        u = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
        u.clear(); u.send_keys(username)
        p = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
        p.clear(); p.send_keys(password + Keys.RETURN)
        wait.until(EC.url_contains("/admin/"))
        driver.get(target_url)
        wait.until(EC.url_contains("/admin/"))
    else:
        log.append("- Already authenticated (no login redirect).")

def recover_if_logged_out(driver, target_url: str, login_url: str, username: str, password: str, wait, log):
    """If the app navigated to /logout/ or /login/, recover gracefully."""
    cur = driver.current_url
    if ("/admin/logout/" in cur) or ("/admin/login/" in cur) or ("/login" in cur):
        log.append("- Detected logged-out state; recovering...")
        login_if_needed(driver, wait, target_url, login_url, username, password, log)

def search_uuid(driver, wait, uid: str, log) -> bool:
    """Search a UUID on the changelist and click the result. Returns True if opened."""
    # Scope strictly to the changelist search form to avoid header links.
    search_form = wait.until(EC.presence_of_element_located((By.ID, "changelist-search")))
    try:
        search_input = search_form.find_element(By.CSS_SELECTOR, "input[name='q']")
    except Exception:
        search_input = search_form.find_element(By.CSS_SELECTOR, "input[type='text']")

    # Clear -> type -> submit
    try:
        search_input.clear()
    except Exception:
        search_input.send_keys(Keys.CONTROL, "a"); search_input.send_keys(Keys.DELETE)
    search_input.send_keys(uid)
    search_input.send_keys(Keys.RETURN)

    # Wait for result row and click the UUID link inside the results table
    try:
        link = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//table[@id='result_list']//a[normalize-space()='{uid}']")
            )
        )
        log.append(f"  - Found exact link for {uid}")
    except Exception:
        # fallback: first link in results table (if link text format differs)
        try:
            link = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "#result_list tbody tr:first-child th a, #result_list tbody tr:first-child td a")
                )
            )
            log.append(f"  - Fallback: clicking first result row for {uid}")
        except Exception:
            log.append(f"  ! No search results for {uid}")
            return False

    link.click()
    wait.until(EC.url_contains("/change/"))
    return True

def clear_duration_and_save(driver, wait, log):
    """On the change form page, clear 'Duration in sec:' and click Save."""
    duration_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//label[normalize-space()='Duration in sec:']/following::input[1]")
        )
    )
    try:
        duration_input.clear()
    except Exception:
        duration_input.send_keys(Keys.CONTROL, "a"); duration_input.send_keys(Keys.DELETE)

    save_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='_save']")))
    save_btn.click()
    wait.until(EC.url_contains("/admin/nkb_resources/unit/"))
    log.append("  - Cleared duration and saved")

def run_job(login_url: str, target_url: str, username: str, password: str, uuids: list[str],
            headless: bool = False, profile_dir: Optional[str] = None) -> str:
    """Orchestrates the full workflow and returns a text log."""
    log = []
    driver = make_driver(headless=headless, profile_dir=profile_dir)
    wait = WebDriverWait(driver, 20)

    try:
        log.append(f"Target list: {target_url}")
        login_if_needed(driver, wait, target_url, login_url, username, password, log)

        for idx, uid in enumerate(uuids, 1):
            try:
                recover_if_logged_out(driver, target_url, login_url, username, password, wait, log)
                driver.get(target_url)
                wait.until(EC.presence_of_element_located((By.ID, "changelist-search")))
                log.append(f"[{idx}/{len(uuids)}] Processing {uid} …")

                opened = search_uuid(driver, wait, uid, log)
                if not opened:
                    log.append(f"   ! Skipping {uid} (not found)")
                    continue

                clear_duration_and_save(driver, wait, log)

                # Go back to base list (clear any filters)
                driver.get(target_url)
                wait.until(EC.presence_of_element_located((By.ID, "changelist-search")))
                log.append(f"   ✓ Done: {uid}")
            except Exception as e:
                log.append(f"   ! Error with {uid}: {e}")
                log.append(traceback.format_exc())
                try:
                    driver.get(target_url)
                except Exception:
                    pass
    finally:
        try:
            # keep the browser open for a brief moment if not headless
            if not headless:
                time.sleep(1.5)
            driver.quit()
        except Exception:
            pass

    return "\n".join(log)

# ------------------ FLASK ROUTES ------------------

@app.get("/")
def index():
    # Prefill common defaults (you can remove if you want a blank form)
    defaults = {
        "login_url": "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/login/",
        "target_url": "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/nkb_resources/unit/",
        "username": "content_loader",
        "password": "",
        "uuids": "",
        "profile_dir": "",  # e.g. /home/you/selenium_profile
        "headless": False
    }
    return render_template_string(FORM_HTML, defaults=defaults)

@app.post("/run")
def run_task():
    login_url  = request.form.get("login_url", "").strip()
    target_url = request.form.get("target_url", "").strip()
    username   = request.form.get("username", "").strip()
    password   = request.form.get("password", "").strip()
    uuids_raw  = request.form.get("uuids", "").strip()
    profile_dir = request.form.get("profile_dir", "").strip()
    headless = bool(request.form.get("headless"))

    # Parse UUIDs: accept newline or comma separated
    parts = [p.strip() for p in uuids_raw.replace(",", "\n").splitlines()]
    uuids = [p for p in parts if p]

    if not (login_url and target_url and username and password and uuids):
        return redirect(url_for("index"))

    log_text = run_job(
        login_url=login_url,
        target_url=target_url,
        username=username,
        password=password,
        uuids=uuids,
        headless=headless,
        profile_dir=profile_dir or None
    )
    return render_template_string(RESULT_HTML, log=log_text)

if __name__ == "__main__":
    # Run locally
    app.run(debug=True)
