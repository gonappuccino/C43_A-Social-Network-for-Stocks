import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
from scipy import stats

class BasePredictionModel:
    """Base class for all prediction models"""
    
    def __init__(self):
        self.window_size = 14  # Window size for moving average
        self.min_data_points = 30  # Minimum data points required for prediction
        
    def _calculate_moving_average(self, prices: List[float]) -> List[float]:
        """Calculate moving average with improved handling of edge cases"""
        if len(prices) < self.window_size:
            return prices
        
        moving_avg = []
        for i in range(len(prices) - self.window_size + 1):
            window = prices[i:i+self.window_size]
            # Use weighted average with more weight on recent prices
            weights = np.linspace(1, 2, self.window_size)
            window_avg = np.average(window, weights=weights)
            moving_avg.append(window_avg)
        
        return moving_avg
    
    def _calculate_confidence(self, prices: List[float]) -> float:
        """Calculate prediction confidence using multiple factors"""
        if len(prices) < self.min_data_points:
            return 0.5  # Medium confidence if insufficient data
            
        recent_prices = prices[-self.min_data_points:]
        
        # Calculate multiple confidence factors
        price_std = np.std(recent_prices)
        price_mean = np.mean(recent_prices)
        
        # Factor 1: Coefficient of variation (lower is better)
        cv = price_std / price_mean if price_mean > 0 else 1.0
        
        # Factor 2: Trend consistency (using linear regression)
        days = np.array(range(len(recent_prices)))
        slope, _, r_value, _, _ = stats.linregress(days, recent_prices)
        trend_consistency = abs(r_value)  # R-squared value
        
        # Factor 3: Recent volatility (using rolling standard deviation)
        rolling_std = pd.Series(recent_prices).rolling(window=5).std().dropna()
        recent_volatility = rolling_std.mean() / price_mean if price_mean > 0 else 1.0
        
        # Combine factors with weights
        confidence = (
            0.4 * (1 - min(cv, 1.0)) +  # Lower volatility is better
            0.4 * trend_consistency +     # Stronger trend is better
            0.2 * (1 - min(recent_volatility, 1.0))  # Lower recent volatility is better
        )
        
        return round(max(0.1, min(0.9, confidence)), 2)

class StockPredictionModel(BasePredictionModel):
    """Model for predicting individual stock prices"""
    
    def predict_future_prices(self, historical_data: List[Dict], days_to_predict: int = 30) -> Tuple[List[Dict], float]:
        """
        Predicts future prices based on historical stock data.
        
        Args:
            historical_data: List of stock price information by date (each item includes timestamp, close)
            days_to_predict: Number of days to predict into the future (default 30 days)
            
        Returns:
            predicted_prices: List of predicted prices (date, price)
            confidence: Prediction confidence (0-1)
        """
        if len(historical_data) < self.min_data_points:
            return [], 0.0
        
        # Extract close prices
        close_prices = [data['close'] for data in historical_data]
        
        # Calculate moving average
        moving_avg = self._calculate_moving_average(close_prices)
        
        # Calculate recent trend using linear regression
        recent_prices = close_prices[-30:]
        days = np.array(range(len(recent_prices)))
        slope, intercept = np.polyfit(days, recent_prices, 1)
        
        # Calculate volatility for prediction
        recent_returns = np.diff(recent_prices) / recent_prices[:-1]
        volatility = np.std(recent_returns)
        
        # Predict future prices
        predicted_prices = []
        last_date = datetime.strptime(historical_data[-1]['timestamp'], '%Y-%m-%d')
        
        for i in range(1, days_to_predict + 1):
            # Base prediction using linear regression
            predicted_day = len(recent_prices) + i
            regression_prediction = slope * predicted_day + intercept
            
            # Add volatility-based random factor
            # Scale volatility by sqrt of days ahead (volatility increases with time)
            volatility_factor = volatility * np.sqrt(i)
            random_factor = np.random.normal(0, volatility_factor * close_prices[-1])
            
            # Combine with moving average trend
            ma_weight = min(i / days_to_predict, 0.5)  # Increasing weight on moving average
            predicted_price = (1 - ma_weight) * regression_prediction + \
                            ma_weight * moving_avg[-1] + \
                            random_factor
            
            # Prevent negative prices
            predicted_price = max(predicted_price, 0.01)
            
            future_date = (last_date + timedelta(days=i)).strftime('%Y-%m-%d')
            predicted_prices.append({
                'date': future_date,
                'price': round(predicted_price, 2)
            })
        
        confidence = self._calculate_confidence(close_prices)
        
        return predicted_prices, confidence
    
class PortfolioPredictionModel(BasePredictionModel):
    """Model for predicting portfolio performance"""
    
    def predict_portfolio_value(self, 
                              portfolio_data: List[Dict], 
                              days_to_predict: int = 30) -> Tuple[List[Dict], float]:
        """
        Predicts future portfolio value based on current holdings and historical data.
        
        Args:
            portfolio_data: List of historical portfolio values by date
            days_to_predict: Number of days to predict into the future
            
        Returns:
            predicted_values: List of predicted portfolio values (date, value)
            confidence: Prediction confidence (0-1)
        """
        if not portfolio_data:
            return [], 0.0
            
        # Extract historical values
        historical_values = [data['value'] for data in portfolio_data]
        
        # Calculate portfolio returns
        returns = np.diff(historical_values) / historical_values[:-1]
        
        # Calculate portfolio statistics
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Predict future values
        predicted_values = []
        last_date = datetime.strptime(portfolio_data[-1]['timestamp'], '%Y-%m-%d')
        current_value = historical_values[-1]
        
        for i in range(1, days_to_predict + 1):
            # Generate random return based on historical distribution
            random_return = np.random.normal(mean_return, std_return)
            
            # Calculate new value
            predicted_value = current_value * (1 + random_return)
            
            future_date = (last_date + timedelta(days=i)).strftime('%Y-%m-%d')
            predicted_values.append({
                'date': future_date,
                'value': round(predicted_value, 2)
            })
        
        confidence = self._calculate_confidence(historical_values)
        
        return predicted_values, confidence

class StockListPredictionModel(BasePredictionModel):
    """Model for predicting stock list performance"""
    
    def predict_stock_list_value(self,
                               stock_list_data: List[Dict],
                               days_to_predict: int = 30) -> Tuple[List[Dict], float]:
        """
        Predicts future stock list value based on current holdings and historical data.
        
        Args:
            stock_list_data: List of historical stock list values by date
            days_to_predict: Number of days to predict into the future
            
        Returns:
            predicted_values: List of predicted stock list values (date, value)
            confidence: Prediction confidence (0-1)
        """
        if not stock_list_data:
            return [], 0.0
            
        # Extract historical values
        historical_values = [data['value'] for data in stock_list_data]
        
        # Calculate returns and statistics
        returns = np.diff(historical_values) / historical_values[:-1]
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Predict future values
        predicted_values = []
        last_date = datetime.strptime(stock_list_data[-1]['timestamp'], '%Y-%m-%d')
        current_value = historical_values[-1]
        
        for i in range(1, days_to_predict + 1):
            # Generate random return based on historical distribution
            random_return = np.random.normal(mean_return, std_return)
            
            # Calculate new value
            predicted_value = current_value * (1 + random_return)
            
            future_date = (last_date + timedelta(days=i)).strftime('%Y-%m-%d')
            predicted_values.append({
                'date': future_date,
                'value': round(predicted_value, 2)
            })
        
        confidence = self._calculate_confidence(historical_values)
        
        return predicted_values, confidence 