
import time


def get_current_nft_fuel(fuel_text):
    return (int(num) for num in fuel_text.split(':')[1].strip().split('/'))


class Reward:
    def __init__(self, token=0.0, position='5th'):
        self.token = token
        self.position = position


class NFT:
    ALLOWED_REWARDS = {
        '1st': 10.0,
        '2nd': 7.5,
        '3rd': 5.0,
        '4th': 3.5,
        '5th': 0.0
    }

    def __init__(self, button):
        self.button = button
        self.total_fuel = 60
        self.fuel = 0
        self.index = 0
        self.rewards = []

    def reduce_fuel(self):
        self.fuel -= 15

    def set_fuel(self, fuel, total):
        self.total_fuel = total
        self.fuel = fuel

    def start_action(self):
        time.sleep(1)
        self.button.click()

    def set_rewards(self, token, position, reward_day):
        if reward_day >= len(self.rewards):
            self.rewards.append([])
        self.rewards[reward_day].append(Reward(token, position))

    def total_rewards(self, reward_day=0):
        if len(self.rewards):
            return sum([reward.token for reward in self.rewards[reward_day]])
        return -1

    def average_rewards(self):
        total = sum(self.total_rewards(reward_day) for reward_day in range(len(self.rewards)))
        return total / len(self.rewards)

    def parse_rewards(self, reward_positions, game):
        if 'planes' in game:
            self.parse_rewards_for_planes(reward_positions)
        else:
            self.parse_rewards_for_cars(reward_positions)

    def parse_rewards_for_cars(self, reward_positions):
        if len(self.rewards):
            return

        reward_day = 0
        races = self.total_fuel / 15
        for index, position_element in enumerate(reward_positions):
            if index > 0 and index % races == 0:
                reward_day += 1
            position = position_element.get_attribute('innerHTML').strip()
            token = NFT.ALLOWED_REWARDS[position]
            self.set_rewards(token, position, reward_day)

    def parse_rewards_for_planes(self, reward_positions):
        if len(self.rewards):
            return

        reward_day = 0
        for index, position_element in enumerate(reward_positions):
            is_total_row = 'total' in position_element.get_attribute('innerHTML').lower()
            is_header = 'position' in position_element.get_attribute('innerHTML').lower()
            if is_total_row:
                continue
            if is_header:
                reward_day += 1
                continue

            position = position_element.get_attribute('innerHTML').strip()
            token = NFT.ALLOWED_REWARDS[position]
            self.set_rewards(token, position, reward_day-1)
