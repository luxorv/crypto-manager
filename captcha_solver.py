from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.expected_conditions import presence_of_element_located, presence_of_all_elements_located
from selenium.webdriver.support.wait import WebDriverWait
from twocaptcha import TwoCaptcha

from models.nft import NFT, get_current_nft_fuel

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


def save_captcha(form):
    image_element = form.find_element(By.XPATH, "//*[local-name() = 'svg']")
    return image_element.screenshot_as_base64


def remove_images():
    for file in os.listdir('./'):
        if file.endswith('.png'):
            os.remove(file)


class CaptchaSolver:
    def __init__(self, driver, game):
        self.toaster_selector = '.toasted.error'
        self.driver = driver
        self.start_btn = ".btn-green"
        self.confirm_btn = ".btn-green"
        self.load_more_selector = '//button[text()="Load More"]'
        self.rewards_section = '.farm'
        self.close_button = "[aria-label='Close']"
        self.nfts = []
        self.game = game

        api_key = '6c3ecd708935eb1f87748772b2fe744f'

        if not api_key:
            raise Exception("Insert your 2Captcha API Key")

        self.solver = TwoCaptcha(api_key, defaultTimeout=160, pollingInterval=5)
        self.init_page_selectors_by_game()

        self.reward_map = {
            '1st': 10.0,
            '2nd': 7.5,
            '3rd': 5.0,
            '4th': 3.5,
            '5th': 0.0
        }

    def solve_captchas(self):
        self.load_all_nfts()
        self.scroll_to_top()
        self.driver.implicitly_wait(4)
        self.filter_nfts_to_run()
        self.get_nft_fuel_elements()
        solved = False

        for index, nft in enumerate(self.nfts):
            nft.index = index
            start_time = time.time()
            previous_fuel = nft.fuel
            while nft.fuel:
                print("Current nft fuel {}/{}; {} time(s) remaining".format(
                    nft.fuel, nft.total_fuel, (nft.fuel / 15)
                ))
                # if previous_fuel == nft.fuel:
                #     end_time = time.time()
                #     print("Current time: {}".format(end_time - start_time))
                #     if (end_time - start_time) > 4000:
                #         solved = False
                self.set_vertical_scroll(nft.button)
                try:
                    if solved:
                        solved = not self.close_modal()
                        nft.reduce_fuel()
                        print("closing the modal")
                    else:
                        nft.start_action()
                        time.sleep(1)
                        form = self.driver.find_element(By.XPATH, '//form')
                        image = save_captcha(form)
                        solved = self.input_answer_into_form(form, image)
                except Exception:
                    print("something went wrong while solving captchas")

    def input_answer_into_form(self, form, image):
        answer = self.solve_single_captcha(image)
        print(answer)
        if not answer:
            self.close_captcha_modal()
            return False

        form.find_element(By.XPATH, '//input').send_keys(answer["code"])
        form.find_element(By.CSS_SELECTOR, self.confirm_btn).click()

        return self.failed_toaster_exists()

    def solve_single_captcha(self, image):
        result = None
        try:
            result = self.solver.normal(image)
        except TimeoutException:
            print("could not solve captcha")
        return result

    def set_vertical_scroll(self, button):
        height = self.driver.get_window_size()['height']
        vertical_location = button.location['y'] - (height/2)
        self.driver.execute_script("window.scrollTo(0, {});".format(vertical_location))

    def close_modal(self):
        while True:
            try:
                close_btns = WebDriverWait(self.driver, 40, poll_frequency=10).until(
                    presence_of_all_elements_located((By.CSS_SELECTOR, self.close_button))
                )
                if len(close_btns):
                    if close_btns[-1].is_enabled():
                        close_btns[-1].click()
                        time.sleep(1)
                        return True
            except TimeoutException:
                print("can't find the close button")
        return False

    def get_nft_fuel_elements(self):
        all_nft_fuel_spans = self.driver.find_elements(By.XPATH, '//span[text()="Fuel: "]')
        all_nft_fuel_spans = all_nft_fuel_spans[-len(self.nfts):]

        for index, fuel_span in enumerate(all_nft_fuel_spans):
            remaining, total = get_current_nft_fuel(fuel_span.text)
            if remaining > 0:
                self.nfts[index].set_fuel(remaining, total)

    def filter_nfts_to_run(self):
        all_start_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.start_btn)

        for index, button in enumerate(all_start_buttons):
            if "start" in button.text.lower() and button.is_enabled():
                print(button.text.lower())
                nft = NFT(button)
                self.nfts.append(nft)

        print(len(self.nfts))

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

    def failed_toaster_exists(self):
        toaster = None
        try:
            toaster = WebDriverWait(self.driver, 3, ignored_exceptions=NoSuchElementException).until(
                presence_of_element_located((By.CSS_SELECTOR, self.toaster_selector))
            )
        except TimeoutException:
            print("can't find the toaster")
        return toaster is None or "invalid" not in toaster.text.lower()

    def close_captcha_modal(self):
        buttons = self.driver.find_elements(By.CSS_SELECTOR, '.btn-red')

        for button in buttons:
            if 'cancel' in button.text.lower():
                button.click()
                time.sleep(1)


if __name__ == '__main__':
    solve_captchas("planes", r'"C:\Program Files\Google\Chrome\Application\chrome.exe"')
    # solve_captchas("cars", '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome')
    # solve_captchas("planes", '/usr/bin/google-chrome')
