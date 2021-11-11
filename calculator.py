def run_calc():
    car_goal = 25
    time_goal_in_weeks = None
    average_earning_per_car = 18
    starting_cars = 18
    price_per_car = 690
    fuel_price = 2
    current_earnings = 82

    result = CryptoGame(
        car_goal,
        time_goal_in_weeks,
        average_earning_per_car,
        starting_cars,
        price_per_car,
        fuel_price,
        current_earnings
    ).calc_total_number_of_weeks()

    print(result)


class CryptoGame:
    def __init__(
            self,
            car_goal=30,
            time_goal_in_weeks=None,
            average_earning_per_car=20,
            starting_cars=1,
            price_per_car=690,
            fuel_price=2,
            current_earnings=0
    ):
        required_fuel_tokens = starting_cars * fuel_price
        self.car_goal = car_goal
        self.time_goal = time_goal_in_weeks
        self.average_earning_per_car = average_earning_per_car
        self.starting_cars = starting_cars
        self.current_cars = starting_cars
        self.average_daily_earnings = starting_cars * average_earning_per_car
        self.total_earnings = current_earnings if current_earnings >= required_fuel_tokens else required_fuel_tokens
        self.price_per_car = price_per_car
        self.unavailable_cars = []
        self.fuel_price = fuel_price

    def calc_daily_earnings(self):
        running_cars = (len(self.unavailable_cars) + self.starting_cars)
        fuel_price = running_cars * self.fuel_price
        self.total_earnings += (self.average_daily_earnings - fuel_price)

        if self.total_earnings >= (self.price_per_car + fuel_price):
            self.total_earnings -= self.price_per_car
            self.unavailable_cars.append(5)

        self.reduce_unavailable_cars()

    def reduce_unavailable_cars(self):
        for idx in range(len(self.unavailable_cars)):
            if idx <= len(self.unavailable_cars):
                self.unavailable_cars[idx] -= 1

                if self.unavailable_cars[idx] == 0:
                    self.current_cars += 1
                    self.average_daily_earnings += self.average_earning_per_car
                    self.unavailable_cars[idx] -= 1
                    print("Car bought now have {} with an average earnings of {} and {} current tokens".format(
                        self.current_cars,
                        self.average_daily_earnings,
                        self.total_earnings
                    ))

    def calc_total_number_of_weeks(self):
        current_week = 1
        while True:
            if self.time_goal is not None and current_week >= self.time_goal:
                return self.end_stats(current_week)

            for current_day in range(1, 8):
                self.calc_daily_earnings()

                if self.current_cars >= self.car_goal:
                    return self.end_stats(current_week)

            print("End of week {} with {} average earnings and a total of {} earnings with {} cars".format(
                current_week,
                self.average_daily_earnings,
                self.total_earnings,
                self.current_cars
            ))
            current_week += 1

    def end_stats(self, total_time_in_weeks):
        return "\nAverage Daily Earnings: {}\nTotal Remaining Earnings: {}\nTotal weeks: {}\nTotal Cars: {}".format(
            self.average_daily_earnings,
            self.total_earnings,
            total_time_in_weeks,
            self.current_cars
        )


run_calc()
