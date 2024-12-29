from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import ttk
import time
import random


def scrape_data(username, password):
    # Initialize WebDriver with options
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Disable automation flags
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)  # Ensure ChromeDriver is in your PATH

    print("Logging in...")
    # Attempt to login
    login_success = login_to_instagram(driver, username, password)

    if not login_success:
        print("Login failed after multiple attempts.")
        driver.quit()
        return

    print("Login successful!")
    time.sleep(5)

    # Navigate to the user's profile page
    driver.get(f"https://www.instagram.com/{username}/")
    time.sleep(random.uniform(3, 5))

    try:
        followers_list = []
        following_list = []

        # Scrape followers
        followers_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers/')]"))
        )
        followers_count = int(followers_link.find_element(By.TAG_NAME, "span").text.replace(",", ""))
        followers_link.click()
        time.sleep(random.uniform(3, 5))
        print("Scraping followers...")
        followers_list = scrape_usernames(driver, followers_count)
        print(f"Followers scraped: {len(followers_list)}")
        print(f"The list of followers: {followers_list}")

        # Scrape following
        driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(random.uniform(3, 5))

        following_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/following/')]"))
        )
        following_count = int(following_link.find_element(By.TAG_NAME, "span").text.replace(",", ""))
        following_link.click()
        time.sleep(random.uniform(3, 5))
        print("Scraping following...")
        following_list = scrape_usernames(driver, following_count)
        print(f"Following scraped: {len(following_list)}")
        print(f"The list of following: {following_list}")

        # Find users not following back
        not_following_back = [user for user in following_list if user not in followers_list]
        print(f"Not following back: {len(not_following_back)}")
        print(f"The list of not following back: {not_following_back}")
        display_ui(not_following_back)

    except Exception as e:
        print(f"Error finding the followers/following links: {e}")

    driver.quit()


def login_to_instagram(driver, username, password, max_retries=3):
    """Attempts to log in to Instagram, retrying if necessary."""
    for attempt in range(max_retries):
        try:
            driver.get("https://www.instagram.com/accounts/login/")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")

            username_field.clear()
            password_field.clear()
            username_field.send_keys(username)
            password_field.send_keys(password)

            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()

            # Wait for login to complete
            WebDriverWait(driver, 10).until(EC.url_contains("instagram.com"))

            # Handle potential popups
            try:
                not_now_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_button.click()
            except Exception:
                pass

            # Login successful
            return True
        except Exception as e:
            print(f"Login attempt {attempt + 1} failed: {e}")
            time.sleep(random.uniform(2, 5))  # Wait before retrying

    return False


def scrape_usernames(driver, total_count):
    """Scroll through the list and extract usernames."""
    usernames = []
    try:
        # Locate the dialog container
        dialog = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
        )

        # Locate the scrollable container inside the dialog using the provided class
        scrollable_content = WebDriverWait(dialog, 10).until(
            EC.presence_of_element_located((By.XPATH, ".//div[contains(@class, 'xyi19xy')]"))
        )

        last_length = 0
        retries = 0  # To prevent infinite retries
        max_additional_retries = 3  # Retry scrolling for extra content
        additional_retries = 0

        while len(usernames) < total_count:
            # Locate the profile links containing usernames
            profile_links = scrollable_content.find_elements(By.XPATH, ".//a[contains(@href, '/')]")
            for link in profile_links:
                href = link.get_attribute("href")
                username = href.split("/")[-2]  # Extract username from the href
                if username and username not in usernames:
                    usernames.append(username)
                    print(f"Added username: {username}")

            print(f"Loaded {len(usernames)} usernames so far...")

            # Scroll down incrementally
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_content)
            time.sleep(random.uniform(2, 4))  # Add delay to allow loading

            # Check if new content has loaded
            new_length = len(usernames)
            if new_length == last_length:
                retries += 1
                print("No new usernames loaded. Retrying...")
                if retries >= 5:
                    # Attempt additional retries if content is still missing
                    additional_retries += 1
                    if additional_retries > max_additional_retries:
                        print("No more content can be loaded.")
                        break
            else:
                retries = 0  # Reset retries if new content is found
            last_length = new_length

        if len(usernames) < total_count:
            print(f"Warning: Only {len(usernames)} out of {total_count} usernames scraped.")

    except Exception as e:
        print(f"Error while scrolling and extracting usernames: {e}")
    return usernames[:total_count]  # Trim to total_count in case of extras


def display_ui(not_following_back):
    """Display the list of people not following back in a GUI."""
    root = tk.Tk()
    root.title("Not Following Back")

    label = tk.Label(root, text="People you follow but who don't follow you back:")
    label.pack(pady=10)

    # Create a scrollable frame
    frame = ttk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    for user in not_following_back:
        user_label = tk.Label(scrollable_frame, text=user, anchor="w")
        user_label.pack(fill=tk.X, padx=10, pady=2)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    root.mainloop()


if __name__ == "__main__":
    # Replace with your credentials
    USERNAME = "your login"  # Replace with your Instagram username
    PASSWORD = "your password"  # Replace with your Instagram password
    scrape_data(USERNAME, PASSWORD)
