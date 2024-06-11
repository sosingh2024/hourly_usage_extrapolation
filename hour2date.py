from datetime import datetime, timedelta

def hour_to_datetime(hour, year):
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        total_hours = 8784  # 
    else:
        total_hours = 8760 

    if hour < 0 or hour >= total_hours:
        return "Invalid hour"

    
    start_of_year = datetime(year, 1, 1)
    result_datetime = start_of_year + timedelta(hours=hour)
    return result_datetime

year = int(input("Enter the year: "))
hour = int(input("Enter the hour of the year (starting from 0): "))

result = hour_to_datetime(hour, year)
print("Datetime:", result)
