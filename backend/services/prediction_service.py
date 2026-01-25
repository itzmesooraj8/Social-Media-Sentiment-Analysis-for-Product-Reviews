from typing import List, Dict, Any
import datetime
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

def generate_forecast(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates a 7-day sentiment forecast based on historical data.
    
    Args:
        history: List of dicts containing 'date' (str YYYY-MM-DD) and 'sentiment' (float -1 to 1).
                 Example: [{'date': '2024-01-01', 'sentiment': 0.5}, ...]
    
    Returns:
        List of dicts for the next 7 days with predicted sentiment.
    """
    if not history:
        return []

    # Convert to DataFrame
    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # If not enough data points for regression, return trend based on last known value
    if len(df) < 2:
        last_val = df.iloc[-1]['sentiment']
        last_date = df.iloc[-1]['date']
        predictions = []
        for i in range(1, 8):
            next_date = last_date + datetime.timedelta(days=i)
            predictions.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "sentiment": last_val
            })
        return predictions

    # Prepare data for Linear Regression
    # Use ordinal dates for regression
    df['date_ordinal'] = df['date'].apply(lambda x: x.toordinal())
    
    X = df[['date_ordinal']].values
    y = df['sentiment'].values

    model = LinearRegression()
    model.fit(X, y)

    # Predict next 7 days
    last_date = df.iloc[-1]['date']
    predictions = []
    
    for i in range(1, 8):
        next_date = last_date + datetime.timedelta(days=i)
        next_date_ordinal = np.array([[next_date.toordinal()]])
        
        predicted_sentiment = model.predict(next_date_ordinal)[0]
        
        # Clamp result between -1.0 and 1.0
        predicted_sentiment = max(-1.0, min(1.0, predicted_sentiment))
        
        predictions.append({
            "date": next_date.strftime("%Y-%m-%d"),
            "sentiment": predicted_sentiment
        })

    return predictions
