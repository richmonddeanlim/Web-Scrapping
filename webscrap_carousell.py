from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import csv # <--- ADDED: Import the csv module

# Setup driver
options = webdriver.ChromeOptions()
# Uncomment the line below to run Chrome in headless mode (without a visible browser UI)
# options.add_argument("--headless")
# Essential for headless mode on some systems
# options.add_argument("--disable-gpu")
# Bypasses OS security model, useful in some containerized environments
# options.add_argument("--no-sandbox")
# Good practice: set a realistic User-Agent to mimic a real browser
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

# URL
search = "Mechanical%20Keyboard"
url = f"https://www.carousell.com.my/search/{search}?addRecent=true&canChangeKeyword=true&includeSuggestions=true&t-search_query_source=direct_search"

# Open the target URL
driver.get(url)

# Initialize WebDriverWait (max 20 seconds wait for elements)
wait = WebDriverWait(driver, 20)

# Close the popup/notification if it exists
# Warning: The class names for this button ('D_sL.D_ayx') are very specific and may change.
print("Checking for and attempting to close notification popup...")
try:
    close_notification_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.D_sQ.D_ayE")))
    close_notification_button.click()
    print("Notification popup closed.")
    time.sleep(1) # Small pause after clicking
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1) # Small pause after clicking
except TimeoutException:
    print("No notification popup found or it didn't appear in time.")
except Exception as e:
    print(f"An error occurred while trying to close the notification: {e}")

# Keep clicking "Show more results" until it's gone
print("\nAttempting to click 'Show more results' button(s)...")
click_count = 0
while True:
    try:
        # Wait for the button to be clickable
        button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show more results')]")))

        # Scroll to the button to ensure it's in view for interaction
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.5) # Small pause after scroll to allow rendering

        button.click()
        click_count += 1
        print(f"Clicked 'Show more results' (Click #{click_count}). Waiting for new content...")

        # Crucial wait: Wait for new content to load. A fixed time.sleep(4) might not be enough
        # or too much. A more robust way would be to wait for the number of product items to increase.
        # For now, keeping your 4-second wait, but be aware this is a potential point of failure.
        time.sleep(4)

    except TimeoutException:
        # This exception is raised by WebDriverWait if the element is not found within the timeout
        print(f"No more 'Show more results' button found after {click_count} clicks (Timeout).")
        break
    except NoSuchElementException:
        # Fallback for if element disappears immediately, though less likely with WebDriverWait
        print(f"No more 'Show more results' button found after {click_count} clicks.")
        break
    except Exception as e:
        print(f"An unexpected error occurred while clicking 'Show more results': {e}")
        break

# Final wait to ensure all dynamically loaded content is on the page
print("Finished clicking 'Show more results'. Performing final content load wait.")
time.sleep(10) # You might adjust this or use a wait for a specific element to appear

# Parse HTML
print("\nParsing page source with BeautifulSoup...")
soup = BeautifulSoup(driver.page_source, "lxml")
# Get all product containers
# WARNING: Class names like "D_qu D_sG" are highly unstable and prone to change frequently
# on dynamic websites like Carousell. If your script breaks, these selectors are the
# most likely culprits. You might need to find more robust identifiers.
products = soup.find_all("div", class_="D_qv D_sL")

print(f"\nFound {len(products)} product containers.")
print("\nScraped Product Names :")

# --- ADDED: Initialize list to store all scraped data ---
all_scraped_data = []
# Add the header row to the list
all_scraped_data.append(['Name', 'Condition', 'Price', 'Product Link'])

found_count = 0
for item in products:
    # WARNING: These classes are highly unstable. Refer to previous explanations for robust selectors.
    name_tag = item.find("p", class_="D_lH D_lI D_lM D_lP D_lS D_lU D_lQ D_me")
    price_tag = item.find("p", class_="D_lH D_lI D_lM D_lO D_lS D_lV D_mc")
    condition_tag = item.find("p", class_="D_lH D_lI D_lM D_lO D_lS D_lU D_me")
    link_elements = item.find_all("a", class_="D_np") # This returns a list of <a> tags

    name = "N/A"
    price = "N/A"
    condition = "N/A"
    product_link = "N/A" # Variable to store the final, full product link

    if name_tag:
        name = name_tag.text.strip()

    if price_tag:
        price = price_tag.text.strip()

    if condition_tag:
        condition = condition_tag.text.strip()

    # User's original logic for link extraction
    # Assumes that link_elements[1] is the correct product link and has an 'href'
    if len(link_elements) > 1 and link_elements[1].get("href"):
        # Prepend 'https://www.' to make it a full, clickable URL
        product_link = f"https://www.carousell.com.my{link_elements[1].get('href')}"


    if name != "N/A" or price != "N/A": # Only process and print if at least name or price found
        # --- ADDED: Store the extracted data into the list ---
        all_scraped_data.append([name, condition, price, product_link])

        print(f"Name : {name}")
        print(f"Condition : {condition}")
        print(f"Price : {price}")
        print(f"Product link : {product_link}\n") # This will print the full URL

        found_count += 1
        
print(f"\nFinished scraping. Found {found_count} products")

# --- ADDED: Write all collected data to a CSV file ---
csv_file_name = "result.csv" # You can change the filename
try:
    with open(csv_file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(all_scraped_data) # Write all rows at once
    print(f"\nSuccessfully saved scraped data to {csv_file_name}")
except Exception as e:
    print(f"\nError saving data to CSV: {e}")

# Done
driver.quit()