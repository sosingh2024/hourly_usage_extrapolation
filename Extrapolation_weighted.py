import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from typicalbaseline import consumption_values as typical_values
from Extrapolation_ARIMA import arima_foi




def calculate_weights(typical_values):
    total_typical_avg = np.mean(typical_values)
    weights = typical_values / total_typical_avg
    return weights

 
def calculate_foi(typical_consumption,actual_consumptions):

 # Create a DataFrame
 data = {
     "Month": pd.Index(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']),
     "Typical Consumption": typical_consumption,
     "Actual Consumption": actual_consumptions
 }
 
 df = pd.DataFrame(data)
 
 # Fill missing values in actual consumption with typical consumption for initial calculations
 df["Actual Consumption"].fillna(df["Typical Consumption"], inplace=True)
 
 df["Average Consumption"] = df[["Typical Consumption", "Actual Consumption"]].mean(axis=1)
 
 # Calculate monthly weightage based on average consumption
 df["Weightage"] = df["Average Consumption"] / df["Average Consumption"].sum()
 
 # FOI for each month
 foi_values = []
 for i in range(len(df)):
   month_i = df.loc[i, "Month"]
   weightage_i = df.loc[i, "Weightage"]
   foi_i = 0
   for j in range(len(df)):
     month_j = df.loc[j, "Month"]
     weightage_j = df.loc[j, "Weightage"]
     if month_i != month_j:
       foi_i += weightage_i * weightage_j
   df.loc[i, "FOI"] = foi_i
   foi_values.append(foi_i)
 
 
 
 foi_array = np.array(foi_values)
 print(foi_array)
 return foi_array





def calculate_diff(all_12_month_typical_avg, typical_values, weights, actual_consumptions):
    diff_sum = 0
    known_months = sum(1 for value in actual_consumptions if value is not None)
    for i, actual_consumption in enumerate(actual_consumptions):
        if actual_consumption is not None:
            diff_sum += weights[i] * typical_values[i]
    return (all_12_month_typical_avg - (diff_sum / known_months))

def extrapolate_monthly_consumption(all_12_month_typical_avg, actual_consumptions, typical_values, foi):
    known_months = sum(1 for value in actual_consumptions if value is not None)
    actual_consumption_avg = np.mean([value for value in actual_consumptions if value is not None])
    weights = calculate_weights(typical_values)
    diff = calculate_diff(all_12_month_typical_avg, typical_values, weights, actual_consumptions)
    extrapolated_consumptions = []
    for i, actual_consumption in enumerate(actual_consumptions):
        if actual_consumption is None:
            extrapolated_consumption = actual_consumption_avg + diff * (weights[i] * foi[i])
        else:
            extrapolated_consumption = actual_consumption
        extrapolated_consumptions.append(extrapolated_consumption)
    return extrapolated_consumptions


months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# typical_values = np.array([500,450,500,600,700,800,900,850,750,650,550,600])
actual_consumptions = [None,None,None,None,None,None,None,500,700,600,None,None]  

#weighted foi
foi = calculate_foi(typical_values,actual_consumptions)
# arima foi
# foi=arima_foi

# Extrapolate monthly consumption
all_12_month_typical_avg = np.mean(typical_values)
extrapolated_consumptions = extrapolate_monthly_consumption(all_12_month_typical_avg, actual_consumptions, typical_values, foi)

for month, extrapolated_consumption in enumerate(extrapolated_consumptions, start=1):
    print(f"Month {month}: Extrapolated Consumption = {extrapolated_consumption}")
