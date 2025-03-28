import numpy as np
from datetime import datetime, timedelta

class StockPredictionModel:
    """
    Simple stock price prediction model
    
    This model uses moving averages and linear regression to perform very basic stock price prediction.
    In a production environment, a more complex model would be needed, but this is sufficient for the purpose of this project.
    """
    
    def __init__(self):
        self.window_size = 14  # Window size for moving average
    
    def predict_future_prices(self, historical_data, days_to_predict=30):
        """
        Predicts future prices based on historical stock data.
        
        Args:
            historical_data: List of stock price information by date (each item includes timestamp, close)
            days_to_predict: Number of days to predict into the future (default 30 days)
            
        Returns:
            predicted_prices: List of predicted prices (date, price)
            confidence: Prediction confidence (0-1)
        """
        if len(historical_data) < self.window_size * 2:
            return [], 0.0
        
        # Extract close prices
        close_prices = [data['close'] for data in historical_data]
        
        # Calculate moving average
        moving_avg = self._calculate_moving_average(close_prices)
        
        # Linear regression for recent trend calculation
        recent_prices = close_prices[-30:]
        days = np.array(range(len(recent_prices)))
        slope, intercept = np.polyfit(days, recent_prices, 1)
        
        # Predict future prices
        predicted_prices = []
        last_date = datetime.strptime(historical_data[-1]['timestamp'], '%Y-%m-%d')
        
        for i in range(1, days_to_predict + 1):
            # Predict using linear regression and recent moving average
            predicted_day = len(recent_prices) + i
            regression_prediction = slope * predicted_day + intercept
            
            # Add some randomness (simulate real market volatility)
            random_factor = np.random.normal(0, 0.01 * close_prices[-1])
            predicted_price = regression_prediction + random_factor
            
            # Prevent negative prices
            predicted_price = max(predicted_price, 0.01)
            
            future_date = (last_date + timedelta(days=i)).strftime('%Y-%m-%d')
            predicted_prices.append({
                'date': future_date,
                'price': round(predicted_price, 2)
            })
        
        # Calculate simple confidence based on recent prediction errors
        confidence = self._calculate_confidence(close_prices)
        
        return predicted_prices, confidence
    
    def _calculate_moving_average(self, prices):
        """Calculate moving average"""
        if len(prices) < self.window_size:
            return prices
        
        moving_avg = []
        for i in range(len(prices) - self.window_size + 1):
            window_avg = sum(prices[i:i+self.window_size]) / self.window_size
            moving_avg.append(window_avg)
        
        return moving_avg
    
    def _calculate_confidence(self, prices):
        """
        Calculate prediction confidence (simple implementation)
        More complex statistical methods should be used in a real-world application
        """
        if len(prices) < 14:
            return 0.5  # Return medium confidence if data is insufficient
        
        # Check recent price volatility
        recent_prices = prices[-14:]
        price_std = np.std(recent_prices)
        price_mean = np.mean(recent_prices)
        
        # Coefficient of variation (lower is more stable)
        cv = price_std / price_mean if price_mean > 0 else 1.0
        
        # Calculate confidence (lower volatility = higher confidence)
        confidence = max(0.1, min(0.9, 1.0 - cv))
        
        return round(confidence, 2) 