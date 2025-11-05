# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from threading import Thread
from datetime import datetime
import uuid
import traceback

# ---------------- Selenium imports ----------------
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

# ---------------------------------------
# 🔧 Your Constants
# ---------------------------------------
LOGIN_URL = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/login/"
TARGET_URL = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/nkb_question/questiontag/?q={}"
USERNAME = "content_loader"
PASSWORD = "CoNmsBzJKd"

# ✅ UPDATED OUTPUT FILE PATH
OUTPUT_FILE_PATH = "/home/nxtwavetech/Videos/config-ops-hub/backend/scripts/originals/question_ids.txt"


# ---------------------------------------
# FastAPI app + CORS
# ---------------------------------------
app = FastAPI(title="Config Ops Hub Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------
# Job registry (console logs)
# ---------------------------------------
class Job:
    def __init__(self):
        self.log = ""
        self.ended = False
        self.started_at = datetime.utcnow()

jobs: Dict[str, Job] = {}

def _log(job: Job, msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    job.log += f"[{ts}] {msg}\n"

# ---------------------------------------
# Request format coming from FRONTEND
# ---------------------------------------
class TagRequest(BaseModel):
    tags: List[str]
    headless: bool = True


# ---------------------------------------
# Selenium logic (unchanged)
# ---------------------------------------
def login(driver, job: Job, username: str, password: str, timeout: int = 30):
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, timeout)

    username_input = wait.until(EC.presence_of_element_located((By.ID, "id_username")))
    password_input = wait.until(EC.presence_of_element_located((By.ID, "id_password")))
    username_input.clear(); username_input.send_keys(username)
    password_input.clear(); password_input.send_keys(password)
    password_input.send_keys(Keys.ENTER)

    try:
        WebDriverWait(driver, 1.5).until(
            EC.any_of(
                EC.url_changes(LOGIN_URL),
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='logout']")),
            )
        )
    except TimeoutException:
        try:
            submit = driver.find_element(By.CSS_SELECTOR, "input[type='submit'],button[type='submit']")
            submit.click()
        except Exception:
            pass

    wait.until(
        EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='logout']")),
            EC.url_contains("/admin/"),
        )
    )
    _log(job, "Login successful.")


def get_question_ids(driver, job: Job, tag: str, timeout: int = 60):
    target_url = TARGET_URL.format(tag)
    driver.get(target_url)

    wait = WebDriverWait(driver, timeout)
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "field-question_id")))
    except TimeoutException:
        _log(job, f"Failed to load page for tag: {tag}")
        return []

    ids = []
    elements = driver.find_elements(By.CLASS_NAME, "field-question_id")
    for elem in elements:
        qid = elem.text.strip()
        if qid:
            ids.append(qid)
            _log(job, f"Found Question ID: {qid}")
    return ids


def save_question_ids_to_file(job: Job, question_ids, file_path):
    try:
        with open(file_path, 'w') as f:
            for qid in question_ids:
                f.write(f"{qid}\n")

        _log(job, f"✅ Question IDs saved to: {file_path}")
    except Exception:
        _log(job, "❌ ERROR writing file:\n" + "".join(traceback.format_exc()))


def selenium_worker(job_id: str, tags: List[str], headless: bool):
    job = jobs[job_id]
    _log(job, f"--- JOB {job_id} START ---")

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")

    driver = None
    all_ids: List[str] = []

    try:
        _log(job, "Launching Chrome WebDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        login(driver, job, USERNAME, PASSWORD)

        for tag in [t.strip() for t in tags if t.strip()]:
            found_ids = get_question_ids(driver, job, tag)
            all_ids.extend(found_ids)
            _log(job, f"Tag '{tag}' → {len(found_ids)} IDs")

    except Exception:
        _log(job, "ERROR:\n" + "".join(traceback.format_exc()))
    finally:
        if driver:
            driver.quit()

    if all_ids:
        save_question_ids_to_file(job, all_ids, OUTPUT_FILE_PATH)
    else:
        _log(job, "⚠️ No IDs found.")

    _log(job, f"--- JOB {job_id} END ---")
    job.ended = True


# ---------------------------------------
# API endpoints (exact naming as frontend)
# ---------------------------------------
@app.post("/tasks/Getting_QuestionIDs_using_tag_names")
def start_tags_job(payload: TagRequest):
    if not payload.tags:
        raise HTTPException(status_code=400, detail="No tags provided.")

    job_id = str(uuid.uuid4())
    jobs[job_id] = Job()

    Thread(target=selenium_worker, args=(job_id, payload.tags, payload.headless), daemon=True).start()

    return {"job_id": job_id, "status": "started"}


@app.get("/tasks/{job_id}/log")
def get_log(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return {"log": job.log}
