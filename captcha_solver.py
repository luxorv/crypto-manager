from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.expected_conditions import presence_of_element_located, presence_of_all_elements_located
from selenium.webdriver.support.wait import WebDriverWait
from twocaptcha import TwoCaptcha

import os
import time
import subprocess


def solve_captchas(game, chrome_path):
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

    captcha_solver = CaptchaSolver(driver, game)
    captcha_solver.solve_captchas()
    driver.close()


def get_current_nft_fuel(fuel_text):
    return (int(num) for num in fuel_text.split(':')[1].strip().split('/'))


def save_captcha(form, captcha_name):
    image_element = form.find_element(By.XPATH, "//*[local-name() = 'svg']")
    image_element.screenshot(captcha_name)


def remove_images():
    for file in os.listdir('./'):
        if file.endswith('.png'):
            os.remove(file)


def print_rewards_for_the_day(rewards_for_the_day):
    total = sum(rewards_for_the_day)
    print("Rewards for the {} with an average of {}".format(total, int(total / len(rewards_for_the_day))))


class CaptchaSolver:
    def __init__(self, driver, game):
        self.toaster_selector = '.toasted.error'
        self.driver = driver
        self.start_btn = ".btn-green"
        self.confirm_btn = ".btn-green"
        self.load_more_selector = '//button[text()="Load More"]'
        self.rewards_section = '.farm'
        self.close_button = "[aria-label='Close']"
        self.start_buttons = []
        self.nft_fuel_spans = []
        self.rewards_for_the_day = []
        self.game = game
        self.reward_map = {
            '1st': 10.0,
            '2nd': 7.5,
            '3rd': 5.0,
            '4th': 3.5,
            '5th': 0.0
        }

        api_key = '<your-key-here>'

        self.solver = TwoCaptcha(api_key, defaultTimeout=160, pollingInterval=5)
        self.init_page_selectors_by_game()

    def solve_captchas(self):
        self.load_all_nfts()
        self.scroll_to_top()
        self.driver.implicitly_wait(40)
        self.filter_nfts_to_run()
        self.get_nft_fuel_elements()
        self.rewards_for_the_day = [0 for _ in range(len(self.start_buttons))]
        self.start_buttons = enumerate(self.start_buttons)

        for index, button in self.start_buttons:
            remaining, total = get_current_nft_fuel(self.nft_fuel_spans[index].text)
            while remaining > 0:
                print("Current nft fuel {}/{}; {} time(s) remaining".format(remaining, total, (remaining / 15)))
                self.set_vertical_scroll(button)
                time.sleep(1)
                button.click()
                try:
                    form = self.driver.find_element(By.XPATH, '//form')
                    captcha_name = 'captcha{}.png'.format(index)
                    save_captcha(form, captcha_name)
                    solved = self.input_answer_into_form(form, captcha_name)
                    if solved:
                        self.close_modal(index)
                except Exception as e:
                    print("something went wrong while solving captchas {}".format(e))

                remaining, total = get_current_nft_fuel(self.nft_fuel_spans[index].text)

        print_rewards_for_the_day(self.rewards_for_the_day)
        remove_images()

    def input_answer_into_form(self, form, captcha_name):
        answer = self.solve_single_captcha(captcha_name)
        print(answer)
        if not answer:
            self.close_captcha_modal()
            return False

        form.find_element(By.XPATH, '//input').send_keys(answer["code"])
        form.find_element(By.CSS_SELECTOR, self.confirm_btn).click()

        return self.failed_toaster_exists()

    def solve_single_captcha(self, captcha_name):
        result = None
        try:
            result = self.solver.normal(captcha_name)
        except TimeoutException:
            print("could not solve captcha")
        return result

    def set_vertical_scroll(self, button):
        height = self.driver.get_window_size()['height']
        vertical_location = button.location['y'] - (height/2)
        self.driver.execute_script("window.scrollTo(0, {});".format(vertical_location))

    def close_modal(self, index):
        try:
            close_btns = WebDriverWait(self.driver, 40).until(
                presence_of_all_elements_located((By.CSS_SELECTOR, self.close_button))
            )
            if len(close_btns):
                close_btns[-1].click()
                self.rewards_for_the_day[index] += self.get_rewards_from_html()
                time.sleep(1)
        except TimeoutException:
            print("can't find the close button")

    def get_rewards_from_html(self):
        if 'planes' in self.game:
            return self.get_rewards_from_planes()
        else:
            return self.get_rewards_from_cars()

    def get_nft_fuel_elements(self):
        all_nft_fuel_spans = self.driver.find_elements(By.XPATH, '//span[text()="Fuel: "]')

        for fuel_span in all_nft_fuel_spans:
            remaining, total = get_current_nft_fuel(fuel_span.text)
            if remaining > 0:
                self.nft_fuel_spans.append(fuel_span)

    def filter_nfts_to_run(self):
        all_start_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.start_btn)

        for button in all_start_buttons:
            if "start" in button.text.lower() and button.is_enabled():
                self.start_buttons.append(button)

    def init_page_selectors_by_game(self):
        if "planes" in self.game:
            self.start_btn = ".btn-red"
            self.confirm_btn = ".btn-green"
            self.load_more_selector = '//span[text()="Load More"]'
            self.close_button = '.btn-blue'

    def load_all_nfts(self):
        while True:
            try:
                load_more = WebDriverWait(self.driver, 3).until(
                    presence_of_element_located((By.XPATH, self.load_more_selector))
                )
                load_more.location_once_scrolled_into_view
                time.sleep(2)
                load_more.click()
            except TimeoutException:
                break

    def scroll_to_top(self):
        self.driver.execute_script("window.scroll(0, 0);")
        time.sleep(1)

    def failed_toaster_exists(self):
        toaster = None
        try:
            toaster = WebDriverWait(self.driver, 3, ignored_exceptions=NoSuchElementException).until(
                presence_of_element_located((By.CSS_SELECTOR, self.toaster_selector))
            )
        except TimeoutException:
            print("can't find the toaster")
        return toaster is None or "invalid" not in toaster.text.lower()

    def get_rewards_from_planes(self):
        reward_btn = self.driver.find_element(By.CSS_SELECTOR, self.close_button)
        reward_html = reward_btn.get_attribute('innerHTML')

        if 'CPAN' not in reward_html:
            return 0

        rewards = reward_html.split('>')[1:]
        for section in rewards:
            if 'CPAN' in section:
                return float(section.split('CPAN')[0].strip())

        return 0

    def get_rewards_from_cars(self):
        reward_section = self.driver.find_element(By.CSS_SELECTOR, '.result-success')
        reward_place = reward_section.get_attribute('innerHTML')
        print(reward_place)
        return self.reward_map[reward_place.lower()]

    def close_captcha_modal(self):
        buttons = self.driver.find_elements(By.CSS_SELECTOR, '.btn-red')

        for button in buttons:
            if 'cancel' in button.text.lower():
                button.click()
                time.sleep(1)


if __name__ == '__main__':
    solve_captchas("planes", '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome')
