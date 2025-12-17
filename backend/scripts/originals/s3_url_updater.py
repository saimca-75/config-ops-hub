# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# # Set up Selenium WebDriver (with a visible browser window)
# def create_driver():
#     options = Options()
#     options.headless = False  # Ensure the browser is visible
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

# # Login to the admin panel using Selenium
# def login_to_admin_panel(driver, login_url, username, password):
#     driver.get(login_url)
#     print(f"Opened: {login_url}")

#     # Wait for the login form to load
#     WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "id_username")))
    
#     # Find the username and password fields and fill them in
#     username_input = driver.find_element(By.ID, "id_username")
#     password_input = driver.find_element(By.ID, "id_password")
#     username_input.send_keys(username)
#     password_input.send_keys(password)
#     password_input.send_keys(Keys.RETURN)

#     # Wait for the page to load and check for a successful login
#     try:
#         # Wait for the <body> element as a generic post-login check
#         WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.TAG_NAME, "body"))
#         )
#         print("Login successful!")
#         return True
#     except Exception as e:
#         print(f"Error: Login failed or took too long. {e}")
#         driver.save_screenshot("login_failed.png")  # Save screenshot for debugging
#         print("Screenshot saved as 'login_failed.png'.")
#         return False

# # Open the target URL and update the multimedia URL
# def update_multimedia_url(driver, base_url, multimedia_id, new_url):
    
#     # Construct the full target URL
#     target_url = f"{base_url}{multimedia_id}/change/"
    
#     # Print the final target URL to check it
#     print(f"Target URL: {target_url}")

#     # Open the target URL
#     driver.get(target_url)
#     print(f"Opened: {target_url}")
    
#     # Wait for the page to load and the "Multimedia URL" input field to appear
#     WebDriverWait(driver, 20).until(
#         EC.presence_of_element_located((By.NAME, "multimedia_url"))
#     )

#     # Find the "Multimedia URL" field and change its value
#     multimedia_url_input = driver.find_element(By.NAME, "multimedia_url")
#     multimedia_url_input.clear()  # Clear any existing URL
#     multimedia_url_input.send_keys(new_url)  # Enter the new S3 URL

#     # Find and click the Save button
#     save_button = driver.find_element(By.XPATH, "//input[@type='submit' or @value='Save']")
#     save_button.click()  # Click the Save button

#     print("Clicked the 'Save' button.")

#     # Wait for the page to confirm the update (e.g., URL change confirmation)
#     time.sleep(5)  # Wait for 5 seconds to observe the change

# # Main function
# def main():
#     LOGIN_URL = "https://nkb-backend-ccbp-gamma.earlywave.in/admin/login/"
#     USERNAME = "content_loader"
#     PASSWORD = "ABIs"
#     BASE_URL = "https://nkb-backend-ccbp-gamma.earlywave.in/admin/nkb_interactive_video/multimedia/"
#     multimedia_id = "0d851f5c-da11-4e4c-b3f4-7784694297ed"  # Given multimedia ID
#     new_url = "https://media-content.ccbp.in/ccbp_prod/media/video_content/niat/niat_classes/build_your_own_dynamic_web_application/english/23-10-2025-introductionToDynamicWebApplications-English-V1/video__extension__"  # S3 URL to change

#     # Initialize the Selenium WebDriver
#     driver = create_driver()

#     # Login to the admin panel
#     if login_to_admin_panel(driver, LOGIN_URL, USERNAME, PASSWORD):
#         # Open the target URL and update the multimedia URL
#         update_multimedia_url(driver, BASE_URL, multimedia_id, new_url)
#     else:
#         print("Failed to login. Please check the screenshot for debugging.")

#     driver.quit()  # Close the browser after the process

# if __name__ == "__main__":
#     main()


# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# # Set up Selenium WebDriver (with a visible browser window)
# def create_driver():
#     options = Options()
#     options.headless = False  # Ensure the browser is visible
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     return driver

# # Login to the admin panel using Selenium
# def login_to_admin_panel(driver, login_url, username, password):
#     driver.get(login_url)
#     print(f"Opened: {login_url}")

#     # Wait for the login form to load
#     WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "id_username")))
    
#     # Find the username and password fields and fill them in
#     username_input = driver.find_element(By.ID, "id_username")
#     password_input = driver.find_element(By.ID, "id_password")
#     username_input.send_keys(username)
#     password_input.send_keys(password)
#     password_input.send_keys(Keys.RETURN)

#     # Wait for the page to load and check for a successful login
#     try:
#         # Wait for the <body> element as a generic post-login check
#         WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.TAG_NAME, "body"))
#         )
#         print("Login successful!")
#         return True
#     except Exception as e:
#         print(f"Error: Login failed or took too long. {e}")
#         driver.save_screenshot("login_failed.png")  # Save screenshot for debugging
#         print("Screenshot saved as 'login_failed.png'.")
#         return False

# # Open the target URL and update the multimedia URL
# def update_multimedia_url(driver, base_url, multimedia_id, new_url):
#     # Construct the full target URL
#     target_url = f"{base_url}{multimedia_id}/change/"
    
#     # Print the final target URL to check it
#     print(f"Target URL: {target_url}")

#     # Open the target URL
#     driver.get(target_url)
#     print(f"Opened: {target_url}")
    
#     # Wait for the page to load and the "Multimedia URL" input field to appear
#     WebDriverWait(driver, 20).until(
#         EC.presence_of_element_located((By.NAME, "multimedia_url"))
#     )

#     # Find the "Multimedia URL" field and change its value
#     multimedia_url_input = driver.find_element(By.NAME, "multimedia_url")
#     multimedia_url_input.clear()  # Clear any existing URL
#     multimedia_url_input.send_keys(new_url)  # Enter the new S3 URL

#     # Find and click the Save button
#     save_button = driver.find_element(By.XPATH, "//input[@type='submit' or @value='Save']")
#     save_button.click()  # Click the Save button

#     print("Clicked the 'Save' button.")

#     # Wait for the page to confirm the update (e.g., URL change confirmation)
#     time.sleep(5)  # Wait for 5 seconds to observe the change

# # Main function
# def main():
#     LOGIN_URL = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/login/"
#     # Beta creds
#     # USERNAME = "content_loader"
#     # PASSWORD = "ABIsA9QTn9"
#     # Gamma Creds
#     # USERNAME = "content_loader"
#     # PASSWORD = "iyKqn1h2BT"
#     # prod creds
#     USERNAME = "content_loader"
#     PASSWORD = "CoNmsBzJKd"
#     BASE_URL = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/nkb_interactive_video/multimedia/"

#     # List of tuples containing (multimedia_id, new_url)
#     multimedia_data = [
#        (
#           "81045cdb-bdb7-46d4-ac47-1524867e6b",
#           "https://media-content.ccbp.in/ccbp_prod/media/video_content/niat/niat_classes/python/23-10-2025-inputOutputBasics-English-V1/video__extension__"
#        ),
#      ]
#     # Initialize the Selenium WebDriver
#     driver = create_driver()

#     # Login to the admin panel
#     if login_to_admin_panel(driver, LOGIN_URL, USERNAME, PASSWORD):
#         # Loop through the multimedia data and update URLs
#         for multimedia_id, new_url in multimedia_data:
#             update_multimedia_url(driver, BASE_URL, multimedia_id, new_url)
#     else:
#         print("Failed to login. Please check the screenshot for debugging.")

#     driver.quit()  # Close the browser after the process

# if __name__ == "__main__":
#     main()
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up Selenium WebDriver (with a visible browser window)
def create_driver():
    options = Options()
    options.headless = False  # Ensure the browser is visible
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Login to the admin panel using Selenium
def login_to_admin_panel(driver, login_url, username, password):
    driver.get(login_url)
    print(f"Opened: {login_url}")

    # Wait for the login form to load
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "id_username")))
    
    # Find the username and password fields and fill them in
    username_input = driver.find_element(By.ID, "id_username")
    password_input = driver.find_element(By.ID, "id_password")
    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)

    # Wait for the page to load and check for a successful login
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Login successful!")
        return True
    except Exception as e:
        print(f"Error: Login failed or took too long. {e}")
        driver.save_screenshot("login_failed.png")
        print("Screenshot saved as 'login_failed.png'.")
        return False

# Open the target URL and update the multimedia URL
def update_multimedia_url(driver, base_url, multimedia_id, new_url):
    # Construct the full target URL
    target_url = f"{base_url}{multimedia_id}/change/"
    
    print(f"Target URL: {target_url}")
    driver.get(target_url)
    
    # Wait for the "Multimedia URL" input field to appear
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "multimedia_url")))

    # Update the multimedia URL
    multimedia_url_input = driver.find_element(By.NAME, "multimedia_url")
    multimedia_url_input.clear()
    multimedia_url_input.send_keys(new_url)

    # Click the Save button
    save_button = driver.find_element(By.XPATH, "//input[@type='submit' or @value='Save']")
    save_button.click()

    print("Clicked the 'Save' button.")
    time.sleep(5)  # Wait to ensure the update is applied

# Main function
def main():
    # LOGIN_URL = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/login/"
    # USERNAME = "content_loader"
    # PASSWORD = "CoN"
    # BASE_URL = "https://nkb-backend-ccbp-prod-apis.ccbp.in/admin/nkb_interactive_video/multimedia/"

    # List of multimedia updates: (multimedia_id, new_url)
    multimedia_data = [("81045cdb-bdb7-46d4-ac47-1524867e6b44","https://media-content.ccbp.in/ccbp_prod/media/video_content/niat/niat_classes/python/23-10-2025-inputOutputBasics-English-V1/video__extension__"),]

    driver = create_driver()

    if login_to_admin_panel(driver, LOGIN_URL, USERNAME, PASSWORD):
        for multimedia_id, new_url in multimedia_data:
            update_multimedia_url(driver, BASE_URL, multimedia_id, new_url)
    else:
        print("Failed to login. Please check the screenshot for debugging.")

    driver.quit()

if __name__ == "__main__":
    main()

