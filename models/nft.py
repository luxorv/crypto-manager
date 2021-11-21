
import time


def get_current_nft_fuel(fuel_text):
    return (int(num) for num in fuel_text.split(':')[1].strip().split('/'))


class NFT:
    def __init__(self, button):
        self.button = button
        self.total_fuel = 60
        self.fuel = 0
        self.rewards = 0
        self.index = 0

    def reduce_fuel(self):
        self.fuel -= 15

    def set_fuel(self, fuel, total):
        self.total_fuel = total
        self.fuel = fuel

    def start_action(self):
        time.sleep(1)
        self.button.click()
