
import time


def get_current_nft_fuel(fuel_text):
    return (int(num) for num in fuel_text.split(':')[1].strip().split('/'))


class NFT:
    def __init__(self, button, index):
        self.button = button
        self.total_fuel = 60
        self.fuel = 0
        self.rewards = 0
        self.index = index

    def reduce_fuel(self):
        self.total_fuel -= 15

    def set_fuel(self, fuel, total):
        self.total_fuel = total
        self.fuel = fuel

    def start_race(self):
        time.sleep(1)
        self.button.click()

