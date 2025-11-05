from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, logging

# ---------------------------------------------
# Configuration
# ---------------------------------------------
LOGIN_URL = "https://nkb-backend-ccbp-beta.earlywave.in/admin/login/"
BASE_URL = "https://nkb-backend-ccbp-beta.earlywave.in/admin/nkb_learning_resource/learningresource/"
USERNAME = "content_loader"
PASSWORD = "ABIsA9QTn9"

# ---------------------------------------------
# Chrome WebDriver Setup (No ChromeDriver path)
# ---------------------------------------------
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument("--headless=new")  # comment this if you want to see Chrome open
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# 👇 No Service(), No ChromeDriverManager, No local path checks
driver = webdriver.Chrome(options=chrome_options)

# ---------------------------------------------
# Core Automation Logic
# ---------------------------------------------
def modify_resource(uuid):
    target_url = f"{BASE_URL}{uuid}/change/"

    try:
        # 1. Log in
        print("Navigating to login page...")
        driver.get(LOGIN_URL)
        time.sleep(2)

        username_field = driver.find_element(By.NAME, 'username')
        password_field = driver.find_element(By.NAME, 'password')

        print(f"Entering credentials for username: {USERNAME}")
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        password_field.send_keys(Keys.RETURN)

        time.sleep(3)
        print("Login successful!")

        # 2. Navigate to resource page
        print(f"Navigating to target page for UUID: {uuid}")
        driver.get(target_url)
        time.sleep(3)

        # 3. Clear specific fields and set double spaces
        fields_to_clear_with_double_space = [
            'title', 'title_en', 'content', 'content_en'
        ]
        for field in fields_to_clear_with_double_space:
            try:
                field_element = driver.find_element(By.NAME, field)
                print(f"Setting field {field} to double spaces.")
                field_element.clear()
                field_element.send_keys("  ")
                time.sleep(1)
            except Exception as e:
                print(f"Could not find or set field {field}: {e}")

        # 4. Fill specific fields with values
        fields_to_fill = {
            'content_format': 'TEXT',
            'content_format_en': 'TEXT',
            'learning_resource_type': 'INTERACTIVE_VIDEO'
        }
        for field, value in fields_to_fill.items():
            try:
                field_element = driver.find_element(By.NAME, field)
                print(f"Filling field: {field} with value: {value}")
                field_element.clear()
                field_element.send_keys(value)
                time.sleep(1)
            except Exception as e:
                print(f"Could not find or fill field {field}: {e}")

        # 5. Wait for and click Save
        print("Waiting for Save button to be visible...")
        save_button = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@value='Save']"))
        )
        print("Saving the changes...")
        save_button.click()

        # 6. Wait and verify result
        print("Waiting 20 seconds for save result...")
        time.sleep(20)

        current_url = driver.current_url
        print(f"Current URL after save: {current_url}")

        try:
            success_message = driver.find_element(By.CLASS_NAME, "success-message-class-name")
            print("Success message found:", success_message.text)
        except Exception:
            print("No success message found or unable to locate it.")

        input("Press Enter to close browser after manual inspection...")

    finally:
        print("Closing the browser...")
        driver.quit()

# ---------------------------------------------
# Example usage
# ---------------------------------------------
uuid_list = ["b31d7aa4-c7d2-4842-b945-d31f6cef9ee9"]

for uuid in uuid_list:
    modify_resource(uuid)
