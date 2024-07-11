import numpy as np
import pandas as pd
import requests
import base64
import matplotlib.pyplot as plt
from datetime import datetime,timedelta
import json
import csv




def genability_values(genability_json_path):
    """
    :param genability_json_path: relative path of json file containing genability hourly values.
    :return Hourly genability value which is required to calculate RMSE & MAPE.
    """
    with open(genability_json_path) as f:
        data=json.load(f)

    genability_hourly_values={}
    date_hourly_consumption = {}
    for entry in data:
        from_datetime = entry['fromDateTime']
        to_datetime = entry['toDateTime']
        quantity_key = entry['quantityKey']
        charge_type = entry['chargeType']
        item_quantity = entry['itemQuantity']


        if charge_type == 'CONSUMPTION_BASED' :
            date = from_datetime+" "+to_datetime
            hour = int(from_datetime.split('T')[1].split(':')[0])
            key=from_datetime+" to "+ to_datetime
            # Update the dictionary withitemQuantity for the date and hour
            
            date_hourly_consumption[(date, hour)] = item_quantity
            genability_hourly_values[key]=item_quantity
            

    return genability_hourly_values




def func(zipcode,addressString,buildingType,customerClass,intervalFromDateTime,intervalToDateTime,extrapolated_hourly_values):
    """
    :param zipcode:ZIP or post code used to look up local buildings .
    :param addressString:Full address of location considered
    :param buildingType:The building type that best describes the building
    :param customerClass:The class of customer, which is one of RESIDENTIAL, GENERAL, or SPECIAL_USE
    :param intervalFromDateTime:By default start of current year.
    :param intervalToDateTime:By default first day of next year.
    :return ndarray containing hourly typical values ranging between intervalFromDateTime to intervalToDateTime.
    """
    endpoint = 'https://api.genability.com/rest/v1/typicals/baselines/best'
    params_hourly= {
            'zipCode':zipcode,
            'addressString':addressString,
            'buildingType':buildingType,
            'excludeMeasures':'false',
            'customerClass':customerClass,
            'intervalFromDateTime':intervalFromDateTime,
            'intervalToDateTime':intervalToDateTime
        }
   
    headers={'Authorization':'Basic YTFiNmMxOTEtMWRjNy00ZTljLTkwNzQtNWZjODU5ZTZjMDkwOjgxZDdjNjc3LTAyNGUtNDFlOC1iZWU0LTY1MDU5YWUzZDc4MA=='}

    response_hourly=requests.get(endpoint, params=params_hourly, headers=headers)
   
    hourly_consumption = {}
    typical_consumption={}
    if response_hourly.status_code == 200:
        data = response_hourly.json()
            

        # Extract the hourly consumption values
        for result in data['results']:
            index=0
            for interval in result['intervals']:
                consumption = interval['kWh']['quantityAmount']
                hour=interval['fromDateTime']+" to "+interval['toDateTime']
                hourly_consumption[hour] = extrapolated_hourly_values[index]
                typical_consumption[hour]=consumption
                index +=1
                   
    else:
        print("Error: Unable to retrieve data. Status code:", response_hourly.status_code)

    return hourly_consumption,typical_consumption


def get_genability_values(genability_json_path):
    """
    :param genability_json_path: relative path of json file containing genability hourly values.
    :return Hourly genability value which is required to calculate RMSE & MAPE.
    """
    with open(genability_json_path) as f:
        data=json.load(f)

    date_hourly_consumption = {}
    for entry in data:
        from_datetime = entry['fromDateTime']
        to_datetime = entry['toDateTime']
        quantity_key = entry['quantityKey']
        charge_type = entry['chargeType']
        item_quantity = entry['itemQuantity']


        if charge_type == 'CONSUMPTION_BASED' :
            date = from_datetime+" "+to_datetime
            hour = int(from_datetime.split('T')[1].split(':')[0])

            # Update the dictionary with summed itemQuantity for the date and hour
            if (date, hour) in date_hourly_consumption:
                date_hourly_consumption[(date, hour)] += item_quantity
                
            else:
                date_hourly_consumption[(date, hour)] = item_quantity
                

    hourly_consumption = np.zeros(8784)   # Change size to 8760 for non-leap year

    # Iterate through the dictionary and update the array with summed itemQuantity for each hour
    index=0
    for key, value in date_hourly_consumption.items():
        date, hour = key 
        hourly_consumption[index] = value
        index=index+1


    return hourly_consumption



def convert_daily_consumption_to_date_map(begin_date,daily_consumption):
    """
    :param daily_consiumption: daily typical consumption ndarray.
    :return map containing date & daily typical usage.
    """
    start_date = begin_date
    date=start_date
    daily_consumption_map = {}
    
    for i, value in enumerate(daily_consumption):
        daily_consumption_map[date] = value
        date=date+timedelta(days=1)
    return daily_consumption_map

def get_net_bill_usage(usage_data):
    """
    :param usage_data: Bill usage entered by customer.
    :return total consumption for all input intervals.
    """
    net_bill_usage = sum(entry['amount'] for entry in usage_data)
    return net_bill_usage

def get_net_typical_usage(usage_data, daily_consumption_map):
    """
    :param usage_data:Bill usage entered by customer.
    :param daily_consumption_map:map containing date & daily typical usage
    :return Total typical consumption corresponding to all intervals.
    """
    net_typical_usage = 0
    for entry in usage_data:
        start_date = entry['start']
        end_date = entry['end']
        # Calculate sum of daily consumption for the corresponding dates
        current_date = start_date
        while current_date <end_date:
            if current_date in daily_consumption_map:
                net_typical_usage += daily_consumption_map[current_date]
            current_date += timedelta(days=1)
    return net_typical_usage

def calculate_extrapolated_consumption(year,hourly_consumption,usage_data, daily_consumption_map, scaling_ratio):
    """
    :param year: current year of analysis
    :param hourly_consumption:ndarray containing hourly typical values
    :param usage_data:Bill usage entered by customer.
    :param daily_consumption_map:map containing date & daily typical usage
    :param scaling_ratio:Net ratio calculated by dividing net_bill_usage by net_typical_usage of all usage bill intervals.
    :return Extrapolated hourly values.
    """
    hourly_consumption_map = {}
    current_date = datetime(year, 1, 1, 0, 0)         
    for value in hourly_consumption:
        hourly_consumption_map[current_date] = value
        current_date += timedelta(hours=1)
    
    extrapolated_hourly_consumption = []

    # Extrapolation for all hours
    for hour, value in hourly_consumption_map.items():
        for entry in usage_data:
            daily_values_within_entry=0
            if entry['start'] <= hour < entry['end']:
                start_date = entry['start']
                end_date = entry['end']
                # Calculate sum of daily consumption for the corresponding entry dates
                current_date = start_date
                while current_date <end_date:
                    if current_date in daily_consumption_map:
                        daily_values_within_entry += daily_consumption_map[current_date]
                    current_date += timedelta(days=1)
                ratio = entry['amount'] / daily_values_within_entry
                extrapolated_hourly_consumption.append(value * ratio)
                break
        else:
            # Hour is not within any usage entry, extrapolate based on the net ratio scaling factor
            extrapolated_hourly_consumption.append(value * scaling_ratio)
        
        
        
    extrapolated_hourly_values = np.array(extrapolated_hourly_consumption)
    return extrapolated_hourly_values

def calculate_rmse_and_mape(genability_hourly_values, extrapolated_hourly_values):
    """
    :param genability_hourly_values:ndarray containing hourly Genability values.
    :param extrapolated_hourly_values:ndarary containing Extrapolated hourly values
    :return RMSE & MAPE.
    """
    n = len(genability_hourly_values)
    rmse = np.sqrt(np.mean((genability_hourly_values - extrapolated_hourly_values) ** 2))
    mape = np.mean(np.abs((genability_hourly_values - extrapolated_hourly_values) / genability_hourly_values)) * 100
    return rmse, mape

def plots(genability_hourly_values, extrapolated_hourly_values):
    """
    :param genability_hourly_values:ndarray containing hourly Genability values.
    :param extrapolated_hourly_values:ndarary containing Extrapolated hourly values
    Plots annual extrapolated  & Genability hourly values as well as plots graph between their difference 
    """
    hours_in_year = range(8784)   # Change range to 8760 for non-leap year

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
    

def get_extrapolated_values(begin_date,daily_consumption,hourly_consumption,usage_data,genability_hourly_values):
    """
    :param:begin_date: beginning date of year of analysis
    :param:daily_consumption:ndarray containing typical daily values
    :param:hourly_consumption:ndarray containing typical hourly values
    :param:usage_data:Bill usage entered by customer
    :param genability_hourly_values:ndarray containing hourly Genability values.
    :return Extrapolated hourly values
    
    """
    # Daily consumption to date map
    daily_consumption_map = convert_daily_consumption_to_date_map(begin_date,daily_consumption)

    # Convert start and end dates to datetime objects
    for entry in usage_data:
        entry['start'] = datetime.fromisoformat(entry['start'][:-6])
        entry['end'] = datetime.fromisoformat(entry['end'][:-6])

    net_bill_usage = get_net_bill_usage(usage_data)

    net_typical_usage = get_net_typical_usage(usage_data, daily_consumption_map)

    scaling_ratio = net_bill_usage / net_typical_usage     # Net ratio

    # Extrapolate monthly consumption
    extrapolated_hourly_values = calculate_extrapolated_consumption(begin_date.year,hourly_consumption,usage_data, daily_consumption_map, scaling_ratio)
    return extrapolated_hourly_values
    
 
def deviated(genability_hourly_values,extrapolated_hourly_values,deviation):
    """
    :param genability_hourly_values:ndarray containing hourly Genability values.
    :param extrapolated_hourly_values: ndarray containing extrapolated values
    :param deviation : absolute difference value 
     Prints those values whose deviation is larger than certain value 
    """   
    index=0
    for value in genability_hourly_values:
      if((extrapolated_hourly_values[index]-value)>=deviation or (extrapolated_hourly_values[index]-value)<=deviation):
        print(index,"Extrapolated: ",extrapolated_hourly_values[index],"Genability: ",value,"Typical: ",hourly_consumption[index],"Diff: ",(extrapolated_hourly_values[index]-value))
    
      index=index+1


    
def get_apirequest(zipcode,addressString,buildingType,customerClass,intervalFromDateTime='2024-01-01',intervalToDateTime='2025-01-01'):
    """
    :param zipcode:ZIP or post code used to look up local buildings .
    :param addressString:Full address of location considered
    :param buildingType:The building type that best describes the building
    :param customerClass:The class of customer, which is one of RESIDENTIAL, GENERAL, or SPECIAL_USE
    :param intervalFromDateTime:By default start of current year.
    :param intervalToDateTime:By default first day of next year.
    :return ndarray containing hourly typical values ranging between intervalFromDateTime to intervalToDateTime.
    """
    endpoint = 'https://api.genability.com/rest/v1/typicals/baselines/best'
    params_hourly= {
            'zipCode':zipcode,
            'addressString':addressString,
            'buildingType':buildingType,
            'excludeMeasures':'false',
            'customerClass':customerClass,
            'intervalFromDateTime':intervalFromDateTime,
            'intervalToDateTime':intervalToDateTime
        }
    


    headers={'Authorization':'Basic YTFiNmMxOTEtMWRjNy00ZTljLTkwNzQtNWZjODU5ZTZjMDkwOjgxZDdjNjc3LTAyNGUtNDFlOC1iZWU0LTY1MDU5YWUzZDc4MA=='}

    response_hourly=requests.get(endpoint, params=params_hourly, headers=headers)
    
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
    
    return typical_hourly_values

def get_typical_consumption(hourly_consumption_response):
    """
    :param hourly_consumption_response:ndarray containing hourly typical response from Baseline API.
    :return  annual hourly consumption & daily consumption ndarrays

    """
    day_hour=0
    daily_consumption=[]  
    daily_usage=0
    for value in hourly_consumption_response:
        if(day_hour==23):
            daily_usage +=value
            daily_consumption.append(daily_usage)
            daily_usage=0
            day_hour=0
        else:
            daily_usage +=value
            day_hour +=1
    
    return hourly_consumption_response[:8784],(np.array(daily_consumption))
    

def get_bill_usage():
    # Extract Bill usage from payload
    usage_data= [{"amount":479,"start":"2024-02-07T00:00:00+05:30","end":"2024-03-08T00:00:00+05:30","type":"usage"},
            {"start":"2024-03-08T00:00:00+05:30","end":"2024-04-08T00:00:00+05:30","amount":500,"type":"usage"},
            {"start":"2024-04-08T00:00:00+05:30","end":"2024-05-08T00:00:00+05:30","amount":508,"type":"usage"},
            {"start":"2024-05-08T00:00:00+05:30","end":"2024-06-08T00:00:00+05:30","amount":520,"type":"usage"},
            {"start":"2024-06-08T00:00:00+05:30","end":"2024-07-08T00:00:00+05:30","amount":540,"type":"usage"},
            {"start":"2024-07-08T00:00:00+05:30","end":"2024-08-08T00:00:00+05:30","amount":534,"type":"usage"},
            {"start":"2024-08-08T00:00:00+05:30","end":"2024-09-08T00:00:00+05:30","amount":523,"type":"usage"},
            {"start":"2024-09-08T00:00:00+05:30","end":"2024-10-08T00:00:00+05:30","amount":538,"type":"usage"}]
    
    return usage_data

def get_toDateTime(usage_data):
    """
    :param usage_data:List of dictionary containing usage bills for intervals.
    :return  intervalToDateTime: DateTime upto which we need to get hourly values from typical baseline

    """
    n=len(usage_data)
    intervalToDateTime=""
    if(datetime.fromisoformat(usage_data[n-1]["end"][:10])<=datetime(2025, 1, 1)):
        intervalToDateTime='2025-01-01'
    else:
        intervalToDateTime=usage_data[n-1]['end'][:10]  #If customer enters usage bill entry  extending to next year.E.g: 5th December 2024-5th Jan 2025

    return intervalToDateTime
           
# Example usecase:Case-4(CA)
usage_data=get_bill_usage()
begin_date=datetime(year=2024, month=1, day=1) # Change acording to year of analysis
intervalToDateTime=get_toDateTime(usage_data)


hourly_consumption_response=get_apirequest('93940','2600 Sand Dunes Dr, Monterey, CA, USA','RESIDENTIAL','RESIDENTIAL','2024-01-01',intervalToDateTime)

hourly_consumption,daily_consumption=get_typical_consumption(hourly_consumption_response)

genability_hourly_values =get_genability_values('./jsonfold/hourly_response_from_genability 1.json')

extrapolated_hourly_values=get_extrapolated_values(begin_date,daily_consumption,hourly_consumption,usage_data,genability_hourly_values)
print("Extrapolated values:",extrapolated_hourly_values)

# Calculate RMSE and MAPE
rmse, mape = calculate_rmse_and_mape(genability_hourly_values, extrapolated_hourly_values)
print("RMSE:", rmse)
print("MAPE:", mape)

# Print values with deviation more than 0.02
# deviated(genability_hourly_values,extrapolated_hourly_values,0.02)

# Draw plots
# plots(genability_hourly_values,extrapolated_hourly_values)




extrapolated_consumption,typical_consumption=func('93940','2600 Sand Dunes Dr, Monterey, CA, USA','RESIDENTIAL','RESIDENTIAL','2024-01-01T00:00:00-08:00','2025-01-01T00:00:00-08:00',extrapolated_hourly_values)
genability_hourly_values = genability_values('./jsonfold/hourly_response_from_genability 1.json')

with open ('dict.csv','w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    for (key, value),(kG,vG),(kt,vt) in zip(extrapolated_consumption.items(),genability_hourly_values.items(),typical_consumption.items()):
        if key[:10]=="2024-03-06" or key[:10]=="2024-03-07" or key[:10]=="2024-03-08":
         writer.writerow([key, value,kG,vG,kt,vt,value-vG])
    
