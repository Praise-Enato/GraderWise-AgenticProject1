# Praise Enato

import math

width = int(input("Enter the width of the tire in mm (ex 205): "))
aspect_ratio = int(input("Enter the aspect ratio of the tire (ex 60): "))
diameter = int(input("Enter the diameter of the wheel in inches (ex 15): "))

tire_volume = (math.pi * (width**2) * aspect_ratio * (width * aspect_ratio + (2540 * diameter))) / 10000000000

print(f"The approximate volume is {tire_volume:.2f} liters")
print()
    
from datetime import datetime

current_date_and_time = datetime.now()
with open("volumes.txt", "at") as volumes_file:
    print(f"{current_date_and_time:%y-%m-%d}, {width},  {aspect_ratio}, {diameter}, {tire_volume:.2f}", file=volumes_file)

purchase_tire = input("Do you want to buy tires with the dimentions you just entered? Type: YES/NO: ")

if purchase_tire.lower() == "yes":
    phone_number = int(input("OK, Please type your phone number: "))
    with open("volumes.txt", "at") as volumes_file:
        print(f"{phone_number}", file=volumes_file)
elif purchase_tire.lower() == "no":
    print("Ok")
else:
    print("Wrong input")
