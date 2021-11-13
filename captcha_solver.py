from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import element_to_be_clickable, presence_of_element_located
from twocaptcha import TwoCaptcha

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


class CaptchaSolver:
    def __init__(self, driver, game):
        self.driver = driver
        self.btn_class = ".btn-green"
        self.load_more_selector = '//button[text()="Load More"]'
        self.close_button = '.close-btn'
        self.start_buttons = []
        self.nft_fuel_spans = []

        api_key = '83e92dace76375a049e6ffd331721ec2'

        self.solver = TwoCaptcha(api_key, defaultTimeout=160, pollingInterval=5)
        self.init_page_selectors_by_game(game)

    def solve_captchas(self):
        self.load_all_nfts()
        self.driver.implicitly_wait(40)
        self.scroll_to_top()
        self.filter_nfts_to_run()

        vertical_scroll = self.get_vertical_scroll()

        self.get_nft_fuel_elements()
        self.start_buttons = enumerate(self.start_buttons)

        for index, button in self.start_buttons:
            remaining, total = get_current_nft_fuel(self.nft_fuel_spans[index].text)
            while remaining > 0:
                print("Current car fuel {}/{}; {} times remaining".format(remaining, total, (remaining/15)))
                self.click_start_button(button, vertical_scroll)
                try:
                    form = self.driver.find_element(By.XPATH, '//form')
                    captcha_name = 'captcha{}.png'.format(index)
                    save_captcha(form, captcha_name)
                    self.input_answer_into_form(form, captcha_name)
                    time.sleep(40)
                    self.close_modal()
                except Exception as e:
                    print("something went wrong while solving captchas {}".format(e.message))

                remaining, total = get_current_nft_fuel(self.nft_fuel_spans[index].text)

    def input_answer_into_form(self, form, captcha_name):
        answer = self.solve_single_captcha(captcha_name)
        form.find_element(By.XPATH, '//input').send_keys(answer["code"])
        form.find_element(By.CSS_SELECTOR, self.btn_class).click()

    def solve_single_captcha(self, captcha_name):
        result = None
        try:
            result = self.solver.normal(captcha_name)
            print(result["code"])
        except Exception as e:
            print("could not solve captcha")
        return result

    def get_vertical_scroll(self):
        amount_of_nfts = len(self.start_buttons)
        amount_of_rows = amount_of_nfts / 3
        remainder = amount_of_nfts % 3

        if remainder != 0:
            amount_of_rows += 1

        window_size = self.driver.get_window_size()
        return int(window_size["height"] / amount_of_rows)

    def close_modal(self):
        close_btns = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label='Close']")
        if len(close_btns):
            close_btns[-1].click()
            time.sleep(1)

    def get_nft_fuel_elements(self):
        all_nft_fuel_spans = self.driver.find_elements(By.XPATH, '//span[text()="Fuel: "]')

        for fuel_span in all_nft_fuel_spans:
            remaining, total = get_current_nft_fuel(fuel_span.text)
            if remaining > 0:
                self.nft_fuel_spans.append(fuel_span)

    def filter_nfts_to_run(self):
        all_start_buttons = self.driver.find_elements(By.CSS_SELECTOR, self.btn_class)

        for button in all_start_buttons:
            if "start" in button.text.lower() and button.is_enabled():
                self.start_buttons.append(button)

    def click_start_button(self, button, vertical_scroll):
        button.location_once_scrolled_into_view
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, window.scrollY - " + str(vertical_scroll) + ")")
        time.sleep(1)
        button.click()
        time.sleep(1)

    def init_page_selectors_by_game(self, game):
        if "planes" in game:
            self.btn_class = ".btn-red"
            self.load_more_selector = '//span[text()="Load More"]'
            self.close_button = "[aria-label='Close']"

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


solve_captchas("cars", '/usr/bin/google-chrome')
