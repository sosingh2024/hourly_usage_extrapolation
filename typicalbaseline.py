import requests
import base64
import numpy as np
import json

def get_monthly_consumption():
    #API endpoint
    endpoint = 'https://api.genability.com/rest/v1/typicals/baselines/best'

    params = {
        'zipCode':'93940',
        'addressString':'2600 Sand Dunes Dr, Monterey, CA 93940, USA',
        'buildingType':'RESIDENTIAL',
        'excludeMeasures':'false',
        'customerClass':'RESIDENTIAL',
        'intervalFromDateTime':'2024-01-01',
        'intervalToDateTime':'2025-01-01',
        'groupBy': 'MONTH'
    }

    headers={'Authorization':'Basic YTFiNmMxOTEtMWRjNy00ZTljLTkwNzQtNWZjODU5ZTZjMDkwOjgxZDdjNjc3LTAyNGUtNDFlOC1iZWU0LTY1MDU5YWUzZDc4MA=='}

    response = requests.get(endpoint, params=params, headers=headers,verify=False)

    
    if response.status_code == 200:
        data = response.json()
        monthly_consumption = {}

        # Extract the monthly consumption values
        month=1
        for result in data['results']:
            for interval in result['intervals']:
                consumption = interval['kWh']['quantityAmount']
                monthly_consumption[month] = consumption
                month +=1

        return monthly_consumption
    else:
        print("Error: Unable to retrieve data. Status code:", response.status_code)
        return None
    
    
def get_daily_consumption():
    #API endpoint
    endpoint = 'https://api.genability.com/rest/v1/typicals/baselines/best'

    params_daily={
        'zipCode':'93940',
        'addressString':'2600 Sand Dunes Dr, Monterey, CA 93940, USA',
        'buildingType':'RESIDENTIAL',
        'excludeMeasures':'false',
        'customerClass':'RESIDENTIAL',
        'intervalFromDateTime':'2024-01-01',
        'intervalToDateTime':'2025-01-01',
        'groupBy': 'DAY'
    }

    headers={'Authorization':'Basic YTFiNmMxOTEtMWRjNy00ZTljLTkwNzQtNWZjODU5ZTZjMDkwOjgxZDdjNjc3LTAyNGUtNDFlOC1iZWU0LTY1MDU5YWUzZDc4MA=='}


    response = requests.get(endpoint, params=params_daily, headers=headers,verify=False)

    
    if response.status_code == 200:
        data = response.json()
        daily_consumption = {}

        # Extract the daily consumption values
        day=1
        for result in data['results']:
            for interval in result['intervals']:
                consumption = interval['kWh']['quantityAmount']
                daily_consumption[day] = consumption
                day +=1

        return daily_consumption
    else:
        print("Error: Unable to retrieve data. Status code:", response.status_code)
        return None
    

def get_hourly_consumption():
    #API endpoint
    endpoint = 'https://api.genability.com/rest/v1/typicals/baselines/best'

    params_hourly= {
        'zipCode':'93940',
        'addressString':'2600 Sand Dunes Dr, Monterey, CA 93940, USA',
        'buildingType':'RESIDENTIAL',
        'excludeMeasures':'false',
        'customerClass':'RESIDENTIAL',
        'intervalFromDateTime':'2024-01-01',
        'intervalToDateTime':'2025-01-01'
    }

    headers={'Authorization':'Basic YTFiNmMxOTEtMWRjNy00ZTljLTkwNzQtNWZjODU5ZTZjMDkwOjgxZDdjNjc3LTAyNGUtNDFlOC1iZWU0LTY1MDU5YWUzZDc4MA=='}


    response = requests.get(endpoint, params=params_hourly, headers=headers,verify=False)

    
    if response.status_code == 200:
        data = response.json()
        with open('hourly_respone.json', 'w') as fout:
            json.dump(data, fout)
        hourly_consumption = {}

        # Extract the hourly consumption values
        hour=1
        for result in data['results']:
            for interval in result['intervals']:
                consumption = interval['kWh']['quantityAmount']
                hourly_consumption[hour] = consumption
                hour +=1

        return hourly_consumption
    else:
        print("Error: Unable to retrieve data. Status code:", response.status_code)
        return None

address = '93940'  
building_type = 'RESIDENTIAL'
monthly_consumption_map = get_monthly_consumption()
# if monthly_consumption_map:
#     print("Monthly typical consumption:")
#     for month, consumption in monthly_consumption_map.items():
#         print("Month:", month, "- Consumption:", consumption)
monthly_values = np.array(list(monthly_consumption_map.values()))

        
daily_consumption_map=get_daily_consumption()
# if daily_consumption_map:
#     print("Daily Typical consumption:")
#     for day, consumption in daily_consumption_map.items():
#         print("Day:",day, "- Consumption:", consumption)
daily_values = np.array(list(daily_consumption_map.values()))


hourly_consumption_map = get_hourly_consumption()
# if hourly_consumption_map:
#     print(" typical Hourly consumption:")
#     for hour, consumption in hourly_consumption_map.items():
#         print("Hour:", hour, "- Consumption:", consumption)
hourly_values=np.array(list(hourly_consumption_map.values()))
print(hourly_values)



