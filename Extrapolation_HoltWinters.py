import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_squared_error
from typicalbaseline import hourly_values as hourly_consumption


mean_value=hourly_consumption.mean()
hourly_consumption=np.concatenate([hourly_consumption,[mean_value]])
 

start_date = pd.to_datetime('2024-01-01')
end_date = pd.to_datetime('2024-12-31')  
date_range = pd.date_range(start=start_date, end=end_date, freq='H')
consumption_series = pd.Series(hourly_consumption, index=date_range)
print(consumption_series)


# Split data 
train_data = hourly_consumption[:int(0.8 * len(hourly_consumption))]
validation_data = hourly_consumption[int(0.8 * len(hourly_consumption)):]

# Define parameter ranges
alpha_range = np.linspace(0.1, 0.9, 5)
beta_range = np.linspace(0.1, 0.9, 5)
gamma_range = np.linspace(0.1, 0.9, 5)

best_mse = float('inf')
best_params = None

# Grid search
for alpha in alpha_range:
    for beta in beta_range:
        for gamma in gamma_range:
            try:
                model = ExponentialSmoothing(train_data)
                fitted_model = model.fit(smoothing_level=alpha, smoothing_slope=beta, smoothing_seasonal=gamma)
                forecast = fitted_model.forecast(len(validation_data))
                mse = mean_squared_error(validation_data, forecast)
                if mse < best_mse:
                    best_mse = mse
                    best_params = (alpha, beta, gamma)
            except:
                continue

print("Best Parameters:", best_params)
# Fit Holt-Winters model with the best parameters
model = ExponentialSmoothing(consumption_series, trend='add', seasonal='add', seasonal_periods=24)
fitted_model = model.fit(smoothing_level=best_params[0], smoothing_slope=best_params[1], smoothing_seasonal=best_params[2])

# Forecast consumption values for the desired period
forecast_values = fitted_model.forecast(steps=30)
print(forecast_values)
