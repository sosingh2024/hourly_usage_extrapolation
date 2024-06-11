import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from typicalbaseline import hourly_values as hourly_consumption


mean_value=hourly_consumption.mean()
hourly_consumption=np.concatenate([hourly_consumption,[mean_value]])
# Convert hourly consumption to a pandas Series with a DatetimeIndex
start_date = pd.to_datetime('2024-01-01')
end_date = pd.to_datetime('2024-12-31', format='%Y-%m-%d')
date_range = pd.date_range(start=start_date, end=end_date, freq='H')
consumption_series = pd.Series(hourly_consumption, index=date_range)

# Aggregate hourly data into monthly sums
monthly_consumption = consumption_series.resample('M').sum()
print(monthly_consumption)

# Fine-tune ARIMA parameters
best_aic = float("inf")
best_order = None

for p in range(3):  
    for d in range(3): 
        for q in range(3): 
            try:
                arima_model = ARIMA(monthly_consumption, order=(p, d, q))
                arima_result = arima_model.fit()
                if arima_result.aic < best_aic:
                    best_aic = arima_result.aic
                    best_order = (p, d, q)
            except:
                continue


arima_model = ARIMA(monthly_consumption, order=best_order)
arima_result = arima_model.fit()

forecast_values = arima_result.forecast(steps=12)

predicted_monthly_values = forecast_values.tolist()
arima_foi=predicted_monthly_values/monthly_consumption.mean()
print(arima_foi)
