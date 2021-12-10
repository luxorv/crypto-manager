from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from models.nft import NFT, get_current_nft_fuel

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

    rewards_collector = RewardCollector(driver, game)
    rewards_collector.collect_rewards()
    driver.close()


def claim_first_reward(claim_buttons):
    if len(claim_buttons):
        current_reward = claim_buttons[0]
        if "fee" in current_reward.get_attribute('innerHTML').lower():
            print("skipping car reward not ready")
        else:
            current_reward.click()
            time.sleep(1)


class RewardCollector:
    def __init__(self, driver, game):
        self.driver = driver
        self.btn_class = ".btn-orange"
        self.load_more_selector = '//button[text()="Load More"]'
        self.close_button = '.close-btn'
        self.rewards_section = '.rewards-section'
        self.reward_position = 'td.uppercase.position-relative'
        self.reward_buttons = []
        self.nfts = []
        self.game = game

        self.init_page_selectors_by_game(game)

    def collect_rewards(self):
        self.driver.implicitly_wait(4)
        self.load_all_nfts()
        self.scroll_to_top()
        self.get_all_claimable_rewards()
        self.get_nft_fuel_elements()

        for index, nft in enumerate(self.nfts):
            nft.index = index
            for num in range(2):
                self.set_vertical_scroll(nft.button)
                nft.start_action()
                time.sleep(1)
                try:
                    self.get_rewards_for_nft(nft.index)
                    all_rewards = self.driver.find_element(By.CSS_SELECTOR, self.rewards_section)
                    claim_buttons = all_rewards.find_elements(By.CSS_SELECTOR, self.btn_class)
                    claim_first_reward(claim_buttons)
                    time.sleep(1)
                except NoSuchElementException:
                    print("skipping nft reward not ready")

                self.close_modal()

        self.print_rewards_from_nfts()

    def set_vertical_scroll(self, button):
        height = self.driver.get_window_size()['height']
        vertical_location = button.location['y'] - (height/2)
        self.driver.execute_script("window.scrollTo(0, {});".format(vertical_location))

    def close_modal(self):
        try:
            self.driver.find_element(By.CSS_SELECTOR, self.close_button).click()
            time.sleep(1)
        except NoSuchElementException:
            print("couldn't close the modal")

    def get_all_claimable_rewards(self):
        all_reward_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.btn_class)

        for index, button in enumerate(all_reward_buttons):
            if "of sold cars" in button.text.lower():
                continue
            if "rewards" in button.text.lower():
                self.nfts.append(NFT(button))

    def init_page_selectors_by_game(self, game):
        if "planes" in game:
            self.btn_class = ".btn-yellow"
            self.load_more_selector = '//span[text()="Load More"]'
            self.close_button = "[aria-label='Close']"
            self.rewards_section = '.rewards-body'
            self.reward_position = '.reward-position'

    def get_rewards_for_nft(self, nft_index):
        reward_positions = self.driver.find_elements(By.CSS_SELECTOR, self.reward_position)
        self.nfts[nft_index].parse_rewards(reward_positions, self.game)

    def load_all_nfts(self):
        while True:
            try:
                load_more = WebDriverWait(self.driver, 3).until(
                    presence_of_element_located((By.XPATH, self.load_more_selector))
                )
                self.driver.execute_script("""
                    let scrollHeight = Math.max(
                        document.body.scrollHeight, document.documentElement.scrollHeight,
                        document.body.offsetHeight, document.documentElement.offsetHeight,
                        document.body.clientHeight, document.documentElement.clientHeight
                    );
                    window.scroll(0, scrollHeight);
                """)
                time.sleep(2)
                load_more.click()
            except TimeoutException:
                break

    def scroll_to_top(self):
        self.driver.execute_script("window.scroll(0, 0);")
        time.sleep(1)

    def print_rewards_from_nfts(self):
        if len(self.nfts):
            accumulated_sum = 0
            for reward_day in range(len(self.nfts[0].rewards)):
                total = sum(nft.total_rewards(reward_day) for nft in self.nfts)
                accumulated_sum += total
                print("Total rewards {} with an average of {} and up now {}"
                      .format(total, total/len(self.nfts), accumulated_sum)
                )

    def get_nft_fuel_elements(self):
        all_nft_fuel_spans = self.driver.find_elements(By.XPATH, '//span[text()="Fuel: "]')
        all_nft_fuel_spans = all_nft_fuel_spans[-len(self.nfts):]

        for index, fuel_span in enumerate(all_nft_fuel_spans):
            remaining, total = get_current_nft_fuel(fuel_span.text)
            if remaining > 0:
                self.nfts[index].set_fuel(remaining, total)


if __name__ == '__main__':
    collect_game_rewards("cars", r'"C:\Program Files\Google\Chrome\Application\chrome.exe"')
    # collect_game_rewards("cars", '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome')
    # collect_game_rewards("cars", '/usr/bin/google-chrome')
