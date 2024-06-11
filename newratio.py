import numpy as np
import pandas as pd
import requests
import base64
import matplotlib.pyplot as plt
from datetime import datetime,timedelta
import json

ratioarr=np.zeros(8784)
count=0

def genability_values(json_path,rotation_hours=0):
    with open(json_path) as f:
        data=json.load(f)

    date_hourly_consumption = {}
    ct=0
    for entry in data:
        from_datetime = entry['fromDateTime']
        to_datetime = entry['toDateTime']
        quantity_key = entry['quantityKey']
        charge_type = entry['chargeType']
        item_quantity = entry['itemQuantity']


        if charge_type == 'CONSUMPTION_BASED' :
            ct=ct+1
            date = from_datetime+" "+to_datetime
            hour = int(from_datetime.split('T')[1].split(':')[0])

            # Update the dictionary with summed itemQuantity for the date and hour
            if (date, hour) in date_hourly_consumption:
                date_hourly_consumption[(date, hour)] += item_quantity
                
            else:
                date_hourly_consumption[(date, hour)] = item_quantity
                # print((date,hour))
                

    hourly_consumption = np.zeros(8784)
    print(ct)

    # Iterate through the dictionary and update the array with summed itemQuantity for each hour
    index=0
    for key, value in date_hourly_consumption.items():
        date, hour = key 
        # print(key,value)
        hourly_consumption[index] = value
        index=index+1


    # print(hourly_consumption)
    # print(hourly_consumption.shape)
    rotated_hourly_consumption=np.roll(hourly_consumption,rotation_hours)
    return rotated_hourly_consumption

def convert_daily_consumption_to_date_map(daily_consumption):
    start_date = datetime(year=2024, month=1, day=1)
    date=start_date
    daily_consumption_map = {}
    
    for i, value in enumerate(daily_consumption):
        daily_consumption_map[date] = value
        date=date+timedelta(days=1)
    return daily_consumption_map

def calculate_total_actual_consumption(usage_data):
    total_actual_consumption = sum(entry['amount'] for entry in usage_data)
    return total_actual_consumption

def calculate_total_daily_consumption(usage_data, daily_consumption_map):
    total_daily_consumption = 0
    for entry in usage_data:
        start_date = entry['start']
        end_date = entry['end']
        # Calculate sum of daily consumption for the corresponding dates
        current_date = start_date
        while current_date <end_date:
            if current_date in daily_consumption_map:
                total_daily_consumption += daily_consumption_map[current_date]
            current_date += timedelta(days=1)
    return total_daily_consumption



def extrapolate_hourly_consumption(hourly_consumption,usage_data, daily_consumption_map, scaling_ratio):
    hourly_consumption_map = {}
    current_date = datetime(2024, 1, 1, 0, 0)
    for value in hourly_consumption:
        hourly_consumption_map[current_date] = value
        current_date += timedelta(hours=1)
    
    extrapolated_hourly_consumption = []
    count=0
    # Extrapolation for all hours
    for hour, value in hourly_consumption_map.items():
        for entry in usage_data:
            daily_values_within_entry=0
            if entry['start'] <= hour < entry['end']:
                # print("within:",hour)
                # print(entry['start'])
                start_date = entry['start']
                end_date = entry['end']
                # Calculate sum of daily consumption for the corresponding entry dates
                current_date = start_date
                while current_date <end_date:
                    if current_date in daily_consumption_map:
                        daily_values_within_entry += daily_consumption_map[current_date]
                    current_date += timedelta(days=1)
                ratio = entry['amount'] / daily_values_within_entry
                ratioarr[count]=ratio
                count +=1
                extrapolated_hourly_consumption.append(value * ratio)
                break
        else:
            # Hour is not within any usage entry, extrapolate based on the net ratio scaling factor
            # print("not within",hour)
            ratioarr[count]=scaling_ratio
            count +=1
            extrapolated_hourly_consumption.append(value * scaling_ratio)
        
        
        
    extrapolated_hourly_values = np.array(extrapolated_hourly_consumption)
    return extrapolated_hourly_values

def calculate_rmse_and_mape(genability_hourly_values, extrapolated_hourly_values):
    n = len(genability_hourly_values)
    print("No of Values:",n)
    rmse = np.sqrt(np.mean((genability_hourly_values - extrapolated_hourly_values) ** 2))
    mape = np.mean(np.abs((genability_hourly_values - extrapolated_hourly_values) / genability_hourly_values)) * 100
    return rmse, mape

def plots(genability_hourly_values, extrapolated_hourly_values):
    
    hours_in_year = range(8784)

    plt.figure(figsize=((25,8)))
    plt.plot(hours_in_year, genability_hourly_values, label='Genability Values', marker='o',markersize=2, linestyle='', color='blue')
    plt.plot(hours_in_year, extrapolated_hourly_values, label='Extrapolated Values', marker='o',markersize=2, linestyle='', color='red')

    plt.xlabel('Hour of the Year')
    plt.ylabel('Consumption')
    plt.title('Variation of Estimated and Actual Hourly Values')
    plt.legend()

    plt.show()

    # Plot the difference between estimated and actual values
    difference = extrapolated_hourly_values - genability_hourly_values
    plt.figure(figsize=(15, 6))
    plt.plot(hours_in_year, difference, label='Difference (Extrapolated - Genability)', color='green')

    plt.xlabel('Hour of the Year')
    plt.ylabel('Difference')
    plt.title('Difference between Estimated and Actual Hourly Values')
    plt.legend()

    plt.show()

scaling_ratio=1
def calc(daily_consumption,hourly_consumption,usage_data,genability_hourly_values):
    # Daily consumption to date map
    daily_consumption_map = convert_daily_consumption_to_date_map(daily_consumption)
    print("Daily_consumption_map:",daily_consumption_map)

    # Convert start and end dates to datetime objects
    for entry in usage_data:
        entry['start'] = datetime.fromisoformat(entry['start'][:-6])
        entry['end'] = datetime.fromisoformat(entry['end'][:-6])
        
    print("Usage_data:",usage_data)

    total_actual_consumption = calculate_total_actual_consumption(usage_data)
    print("Total_actual_consumption:",total_actual_consumption)

    total_daily_consumption = calculate_total_daily_consumption(usage_data, daily_consumption_map)
    print("Corresponding typical consumption:",total_daily_consumption)

    scaling_ratio = total_actual_consumption / total_daily_consumption

    # Extrapolate monthly consumption
    extrapolated_hourly_values = extrapolate_hourly_consumption(hourly_consumption,usage_data, daily_consumption_map, scaling_ratio)
    print("Extrapolation here:",extrapolated_hourly_values)

    # Calculate RMSE and MAPE
    rmse, mape = calculate_rmse_and_mape(genability_hourly_values, extrapolated_hourly_values)

    print("RMSE:", rmse)
    print("MAPE:", mape)
    
    index=0
    for value in genability_hourly_values:
      if((extrapolated_hourly_values[index]-value)>=0.02 or (extrapolated_hourly_values[index]-value)<=-0.02):
        print(index,"Extrapolated: ",extrapolated_hourly_values[index],"Genability: ",value,"Typical: ",hourly_consumption[index],"Diff: ",(extrapolated_hourly_values[index]-value))
    
      index=index+1
    
    
    
    
    plots(genability_hourly_values,extrapolated_hourly_values)
    



    
def apirequest(zipcode,addressString,intervalToDateTime='2025-01-01'):
    endpoint = 'https://api.genability.com/rest/v1/typicals/baselines/best'
    params_hourly= {
            'zipCode':zipcode,
            'addressString':addressString,
            'buildingType':'RESIDENTIAL',
            'excludeMeasures':'false',
            'customerClass':'RESIDENTIAL',
            'intervalFromDateTime':'2024-01-01',
            'intervalToDateTime':'2025-01-01'
        }
    params_daily= {
            'zipCode':zipcode,
            'addressString':addressString,
            'buildingType':'RESIDENTIAL',
            'excludeMeasures':'false',
            'customerClass':'RESIDENTIAL',
            'intervalFromDateTime':'2024-01-01',
            'intervalToDateTime':intervalToDateTime,
            'groupBy':'DAY'
        }
    params_monthly= {
            'zipCode':zipcode,
            'addressString':addressString,
            'buildingType':'RESIDENTIAL',
            'excludeMeasures':'false',
            'customerClass':'RESIDENTIAL',
            'intervalFromDateTime':'2024-01-01',
            'intervalToDateTime':'2025-01-01',
            'groupBy':'MONTH'
        }


    headers={'Authorization':'Basic YTFiNmMxOTEtMWRjNy00ZTljLTkwNzQtNWZjODU5ZTZjMDkwOjgxZDdjNjc3LTAyNGUtNDFlOC1iZWU0LTY1MDU5YWUzZDc4MA=='}

    response_hourly=requests.get(endpoint, params=params_hourly, headers=headers,verify=False)
    response_daily =requests.get(endpoint, params=params_daily, headers=headers,verify=False)
    response_monthly=requests.get(endpoint, params=params_monthly, headers=headers,verify=False)

    hourly_consumption = {}
    if response_hourly.status_code == 200:
        data = response_hourly.json()
            

        # Extract the hourly consumption values
        hour=1
        for result in data['results']:
            for interval in result['intervals']:
                consumption = interval['kWh']['quantityAmount']
                hourly_consumption[hour] = consumption
                hour +=1
            

            
    else:
        print("Error: Unable to retrieve data. Status code:", response_hourly.status_code)

    typical_hourly_values=np.array(list(hourly_consumption.values()))
    print("Typical hourly values :",typical_hourly_values)





    daily_consumption = {}
    if response_daily.status_code == 200:
        data = response_daily.json()
            

        day=1
        for result in data['results']:
            for interval in result['intervals']:
                consumption = interval['kWh']['quantityAmount']
                daily_consumption[day] = consumption
                day +=1
            

            
    else:
        print("Error: Unable to retrieve data. Status code:", response_daily.status_code)

    typical_daily_values=np.array(list(daily_consumption.values()))





    monthly_consumption={}
    if response_monthly.status_code == 200:
        data = response_monthly.json()
            

        # Extract the hourly consumption values
        month=1
        for result in data['results']:
            for interval in result['intervals']:
                consumption = interval['kWh']['quantityAmount']
                monthly_consumption[month] = consumption
                month +=1
            

            
    else:
        print("Error: Unable to retrieve data. Status code:", response_monthly.status_code)

    typical_monthly_values=np.array(list(monthly_consumption.values()))
    return typical_hourly_values,typical_daily_values,typical_monthly_values





hourly_consumption,daily_consumption,monthly_typical_consumption=apirequest('93940','2600 Sand Dunes Dr, Monterey, CA, USA')

usage_data =[{"amount":500,"start":"2024-05-06T00:00:00+05:30","end":"2024-06-07T00:00:00+05:30","type":"usage"},
             {"start":"2024-06-07T00:00:00+05:30","end":"2024-07-07T00:00:00+05:30","amount":520,"type":"usage"},
             {"start":"2024-07-07T00:00:00+05:30","end":"2024-08-07T00:00:00+05:30","amount":509,"type":"usage"},
             {"start":"2024-08-07T00:00:00+05:30","end":"2024-09-07T00:00:00+05:30","amount":540,"type":"usage"}] 
genability_hourly_values = genability_values('./jsonfold/CA24_more_months_hourly_response_genability_CA_1.json',0)

calc(daily_consumption,hourly_consumption,usage_data,genability_hourly_values)
ratio=(ratioarr[3014]+scaling_ratio)/2
var1=hourly_consumption[3014]
var1=var1*ratio
print(var1,genability_hourly_values[3014])

        