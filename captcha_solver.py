from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from PIL import Image
from io import BytesIO
from decoder import decoder

import time
import subprocess


def run_solver(game):
    driver, url = create_driver(game)
    driver.get(url)
    driver.maximize_window()
    driver.implicitly_wait(10)

    btn_class, load_more_selector, close_button, rewards_section = get_page_selectors(game)
    load_all_nfts(driver, load_more_selector)
    scroll_to_top(driver)

    solve_captchas(driver, rewards_section, btn_class)

    driver.close()


def create_driver(game):
    subprocess.Popen(
        '/usr/bin/google-chrome --remote-debugging-port=9222',
        shell=True
    )

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    url = "https://cryptocars.me/play/#/cars" if game == "cars" else "https://cryptoplanes.me/play/#/planes"
    driver = webdriver.Chrome(options=chrome_options)

    return driver, url


def scroll_to_top(driver):
    driver.execute_script("window.scroll(0, 0);")
    time.sleep(1)


def get_page_selectors(game):
    btn_class = ".btn-green"
    load_more_selector = '//button[text()="Load More"]'
    close_button = '.close-btn'
    rewards_section = '.rewards-section'

    if game == "planes":
        btn_class = ".btn-red"
        load_more_selector = '//span[text()="Load More"]'
        close_button = "[aria-label='Close']"
        rewards_section = '.rewards-body'

    return btn_class, load_more_selector, close_button, rewards_section


def solve_captchas(driver, rewards_section, btn_class):
    buttons = driver.find_elements(By.CSS_SELECTOR, btn_class)

    print(len(buttons))

    for button in buttons:
        if "of sold cars" in button.text.lower():
            continue
        if "start" in button.text.lower():
            button.location_once_scrolled_into_view
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, window.scrollY - 400)")
            time.sleep(1)
            button.click()
            time.sleep(2)

            form = driver.find_element(By.XPATH, '//form')
            solve_captcha(driver, form, rewards_section, btn_class)
            break


def solve_captcha(driver, form, rewards_section, btn_class):
    try:
        image = form.find_element(By.XPATH, "//*[local-name() = 'svg']")
        answer = decoder(Image.open(BytesIO(image.screenshot_as_png)))
        print(answer)
        # all_rewards = driver.find_element(By.CSS_SELECTOR, rewards_section)
        # reward_buttons = all_rewards.find_elements(By.CSS_SELECTOR, btn_class)
        # print(reward_buttons)
        # if len(reward_buttons):
        #     current_reward = reward_buttons[0]
        #     print(current_reward.text)
        #     if "fee" in current_reward.get_attribute('innerHTML').lower():
        #         print("skipping car reward not ready")
        #     else:
        #         current_reward.click()
    except NoSuchElementException:
        print("skipping car reward not ready")


def load_all_nfts(driver, load_more_selector):
    while True:
        try:
            load_more = driver.find_element(By.XPATH, load_more_selector)
            load_more.location_once_scrolled_into_view
            time.sleep(2)
            load_more.click()
        except NoSuchElementException:
            break


run_solver("cars")

# try:
#     all_rewards = driver.find_element(By.CSS_SELECTOR, rewards_section)
#     reward_buttons = all_rewards.find_elements(By.CSS_SELECTOR, btn_class)
#     print(reward_buttons)
#     if len(reward_buttons):
#         current_reward = reward_buttons[0]
#         print(current_reward.text)
#         if "fee" in current_reward.get_attribute('innerHTML').lower():
#             print("skipping car reward not ready")
#         else:
#             current_reward.click()
# except NoSuchElementException:
#     print("skipping car reward not ready")
#
# try:
#     driver.find_element(By.CSS_SELECTOR, close_button).click()
#     time.sleep(1)
# except NoSuchElementException:
#     print("skipping car reward not ready")

