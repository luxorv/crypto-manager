from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import time
import subprocess


def collect_game_rewards(game, chrome_path):
    subprocess.Popen(
        chrome_path + ' --remote-debugging-port=9222',
        shell=True
    )

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    url = "https://cryptocars.me/play/#/cars" if game == "cars" else "https://cryptoplanes.me/play/#/planes"
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    driver.maximize_window()
    driver.implicitly_wait(10)

    rewards_collector = RewardCollector(driver, game)
    rewards_collector.collect_rewards()
    driver.close()


class RewardCollector:
    def __init__(self, driver, game):
        self.driver = driver
        self.btn_class = ".btn-orange"
        self.load_more_selector = '//button[text()="Load More"]'
        self.close_button = '.close-btn'
        self.rewards_section = '.rewards-section'
        self.reward_buttons = []

        self.init_page_selectors_by_game(game)

    def collect_rewards(self):
        self.load_all_nfts()
        self.scroll_to_top()
        self.get_all_claimable_rewards()

        vertical_scroll = self.get_vertical_scroll()
        self.reward_buttons = enumerate(self.reward_buttons)

        for index, button in self.reward_buttons:
            for num in range(2):
                self.click_reward_button(button, vertical_scroll)
                try:
                    all_rewards = self.driver.find_element(By.CSS_SELECTOR, self.rewards_section)
                    claim_buttons = all_rewards.find_elements(By.CSS_SELECTOR, self.btn_class)
                    RewardCollector.claim_first_reward(claim_buttons)
                    time.sleep(1)
                except NoSuchElementException:
                    print("skipping car reward not ready")

                self.close_modal()

    def get_vertical_scroll(self):
        amount_of_nfts = len(self.reward_buttons)
        amount_of_rows = amount_of_nfts / 3
        remainder = amount_of_nfts % 3

        if remainder != 0:
            amount_of_rows += 1

        window_size = self.driver.get_window_size()
        return int(window_size["height"] / amount_of_rows)

    def close_modal(self):
        try:
            self.driver.find_element(By.CSS_SELECTOR, self.close_button).click()
            time.sleep(1)
        except NoSuchElementException:
            print("couldn't close the modal")

    def get_all_claimable_rewards(self):
        all_reward_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.btn_class)

        for button in all_reward_buttons:
            if "of sold cars" in button.text.lower():
                continue
            if "rewards" in button.text.lower():
                self.reward_buttons.append(button)

    def click_reward_button(self, button, vertical_scroll):
        button.location_once_scrolled_into_view
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, window.scrollY - " + str(vertical_scroll) + ")")
        time.sleep(1)
        button.click()
        time.sleep(1)

    def init_page_selectors_by_game(self, game):
        if "planes" in game:
            self.btn_class = ".btn-yellow"
            self.load_more_selector = '//span[text()="Load More"]'
            self.close_button = "[aria-label='Close']"
            self.rewards_section = '.rewards-body'

    def load_all_nfts(self):
        while True:
            try:
                load_more = self.driver.find_element(By.XPATH, self.load_more_selector)
                load_more.location_once_scrolled_into_view
                time.sleep(2)
                load_more.click()
            except NoSuchElementException:
                break

    def scroll_to_top(self):
        self.driver.execute_script("window.scroll(0, 0);")
        time.sleep(1)

    @staticmethod
    def claim_first_reward(claim_buttons):
        if len(claim_buttons):
            current_reward = claim_buttons[0]
            if "fee" in current_reward.get_attribute('innerHTML').lower():
                print("skipping car reward not ready")
            else:
                current_reward.click()


collect_game_rewards("cars", '/usr/bin/google-chrome')
