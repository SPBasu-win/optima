from prophet import Prophet
import pandas as pd

def forecast_demand(past_sales: list[int]):
    df = pd.DataFrame({
        "ds": pd.date_range(start="2024-01-01", periods=len(past_sales), freq="D"),
        "y": past_sales
    })

    model = Prophet()
    model.fit(df)

    future = model.make_future_dataframe(periods=7)  # Forecast next 7 days
    forecast = model.predict(future)

    return forecast[["ds", "yhat"]].tail(7).to_dict(orient="records")
