from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os


def get_deck_links(username, password, collectionurl):
    output_path = os.path.join("gitignore", "decklist.csv")

    # Set up headless browser
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        # Step 1: Go to login page
        driver.get("https://cards.ucalgary.ca/login")
        time.sleep(2)

        # Step 2: Fill out and submit the login form
        driver.find_element("name", "username").send_keys(username)
        driver.find_element("name", "password").send_keys(password)
        driver.find_element("name", "login").click()
        time.sleep(3)

        # Step 3: Navigate to collection page
        driver.get(collectionurl)
        time.sleep(3)

        # Step 4: Extract links
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        anchors = soup.select("a.deck-details")
        full_urls = ["https://cards.ucalgary.ca" + a['href'] for a in anchors if a.has_attr("href")]

        # Step 5: Save to CSV
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(",".join(full_urls))

        print(f"✅ {len(full_urls)} full URLs saved (with query params) to {output_path}")

    finally:
        driver.quit()
