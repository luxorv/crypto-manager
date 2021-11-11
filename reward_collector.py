from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


import time
import subprocess

subprocess.Popen(
    '/usr/bin/google-chrome --remote-debugging-port=9222',
    shell=True
)

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

btn_class = "btn-orange"
load_more_selector = '//button[text()="Load More"]'
close_button = '.close-btn'
rewards_section = '.rewards_section'

url = "https://cryptoplanes.me/play/#/planes"
driver = webdriver.Chrome(options=chrome_options)
driver.get(url)
driver.maximize_window()
driver.implicitly_wait(10)

if "planes" in url:
    btn_class = ".btn-yellow"
    load_more_selector = '//span[text()="Load More"]'
    close_button = "[aria-label='Close']"
    rewards_section = '.rewards-body'

while True:
    try:
        load_more = driver.find_element(By.XPATH, load_more_selector)
        load_more.location_once_scrolled_into_view
        time.sleep(2)
        load_more.click()
    except NoSuchElementException:
        break

driver.execute_script("window.scroll(0, 0);")
time.sleep(1)
buttons = driver.find_elements(By.CSS_SELECTOR, btn_class)

print(len(buttons))

for button in buttons:
    if "of sold cars" in button.text.lower():
        continue
    if "rewards" in button.text.lower():
        button.location_once_scrolled_into_view
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, window.scrollY - 400)")
        time.sleep(1)
        button.click()
        time.sleep(2)

        try:
            all_rewards = driver.find_element(By.CSS_SELECTOR, rewards_section)
            reward_buttons = all_rewards.find_elements(By.CSS_SELECTOR, btn_class)
            if len(reward_buttons):
                current_reward = reward_buttons[0]
                if "fee" in current_reward.get_attribute('innerHTML').lower():
                    print("skipping car reward not ready")
                else:
                    current_reward.click()
        except NoSuchElementException:
            print("skipping car reward not ready")

        try:
            driver.find_element(By.CSS_SELECTOR, close_button).click()
            time.sleep(1)
        except NoSuchElementException:
            print("skipping car reward not ready")

driver.close()



