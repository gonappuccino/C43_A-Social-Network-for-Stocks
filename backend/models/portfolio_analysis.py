import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class PortfolioAnalyzer:
    """
    Base class for portfolio analysis
    
    Provides functionality to calculate and analyze statistics of stock lists
    """
    
    def __init__(self):
        self.market_symbol = 'SPY'  # Use S&P 500 ETF as market indicator
    
    def calculate_statistics(self, stock_data, time_period=90):
        """
        Calculates statistics for stock data.
        
        Args:
            stock_data: Dictionary of stock price information by symbol
                {symbol: [{timestamp, open, high, low, close, volume}, ...], ...}
            time_period: Period of historical data to use for analysis (days) (default 90 days)
            
        Returns:
            stats: Dictionary containing calculated statistics
        """
        if not stock_data or self.market_symbol not in stock_data:
            return {
                'stocks': [],
                'correlation_matrix': []
            }
        
        # Prepare dataframe for analysis
        symbols = list(stock_data.keys())
        close_prices = {}
        
        # Extract closing prices for each symbol
        for symbol in symbols:
            if not stock_data[symbol]:
                continue
                
            # Use only data for the required period
            recent_data = stock_data[symbol][-time_period:]
            if len(recent_data) < 14:  # Minimum data requirement
                continue
                
            close_prices[symbol] = [data['close'] for data in recent_data]
        
        # Create dataframe
        price_df = pd.DataFrame(close_prices)
        
        # Calculate daily returns
        returns_df = price_df.pct_change().dropna()
        
        # Calculate beta and coefficient of variation
        market_returns = returns_df[self.market_symbol] if self.market_symbol in returns_df.columns else None
        
        # List to store results
        stock_stats = []
        
        for symbol in returns_df.columns:
            if symbol == self.market_symbol:
                continue
                
            stock_returns = returns_df[symbol]
            
            # Calculate coefficient of variation (COV) - standard deviation/mean
            mean_return = stock_returns.mean()
            std_return = stock_returns.std()
            cov = std_return / abs(mean_return) if mean_return != 0 else np.nan
            
            # Calculate beta (relationship with market)
            beta = np.nan
            if market_returns is not None:
                covariance = stock_returns.cov(market_returns)
                market_variance = market_returns.var()
                beta = covariance / market_variance if market_variance != 0 else np.nan
            
            stock_stats.append({
                'symbol': symbol,
                'cov': round(float(cov), 4) if not np.isnan(cov) else None,
                'beta': round(float(beta), 4) if not np.isnan(beta) else None
            })
        
        # Calculate correlation matrix
        correlation_matrix = []
        if not returns_df.empty and len(returns_df.columns) > 1:
            corr_matrix = returns_df.corr().values.tolist()
            correlation_matrix = [[round(val, 4) for val in row] for row in corr_matrix]
        
        return {
            'stocks': stock_stats,
            'correlation_matrix': correlation_matrix
        }
    
    def calculate_portfolio_value(self, portfolio_stocks, current_prices):
        """
        Calculates the current value of a portfolio.
        
        Args:
            portfolio_stocks: List of stocks in the portfolio
                [{symbol, num_shares}, ...]
            current_prices: Dictionary of current prices by stock symbol
                {symbol: price, ...}
                
        Returns:
            Total portfolio value (stock value)
        """
        total_value = 0.0
        
        for stock in portfolio_stocks:
            symbol = stock['symbol']
            shares = stock['num_shares']
            
            if symbol in current_prices:
                stock_value = shares * current_prices[symbol]
                total_value += stock_value
        
        return round(total_value, 2) 