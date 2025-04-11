import psycopg2
import yfinance as yf
import datetime
import time
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from queries.utils import decimal_to_float as d2f
from typing import Tuple, List, Dict

class StockData:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='template1',
        user='postgres',
        password='2357'
    )

    def fetch_and_store_daily_info_yahoo(self, symbol, num_days=1):
        cursor = self.conn.cursor()
        
        # Verify symbol exists in Stocks table
        verify_symbol_query = '''
            SELECT symbol
            FROM Stocks
            WHERE symbol = %s;
        '''
        cursor.execute(verify_symbol_query, (symbol,))
        if not cursor.fetchone():
            cursor.close()
            return None
        
        # Get the most recent date from DailyStockInfo
        recent_date_query = '''
            SELECT MAX(timestamp) 
            FROM DailyStockInfo
            WHERE symbol = %s;
        '''
        cursor.execute(recent_date_query, (symbol,))
        latest_date = cursor.fetchone()[0]
        
        # If no data in DailyStockInfo, get most recent date from StocksHistory
        if not latest_date:
            history_date_query = '''
                SELECT MAX(timestamp) 
                FROM StocksHistory
                WHERE symbol = %s;
            '''
            cursor.execute(history_date_query, (symbol,))
            latest_date = cursor.fetchone()[0]
        
        adjustment_ratio = 1
        # Calculate the start date (day after the most recent date)
        if latest_date:
            start_date = latest_date
            day_after_start_date = start_date + datetime.timedelta(days=1)
            # Format for Yahoo Finance API
            start_date_str = start_date.strftime('%Y-%m-%d')
            day_after_start_date_str = day_after_start_date.strftime('%Y-%m-%d')

            our_price = self.view_stock_info(symbol, '5d')
            if our_price:
                our_price = our_price[0][4]  # Get the close price from the first row
                
                # Fetch Yahoo Finance data for the same date
                yf_data = yf.Ticker(symbol).history(start=start_date_str, end=day_after_start_date_str)
                if not yf_data.empty:
                    yf_price = float(yf_data['Close'].iloc[0])
                    # Adjusts in case stock was split between 2018 (end of historical data) and now
                    adjustment_ratio = our_price / yf_price
                else:
                    adjustment_ratio = 1
            else:
                adjustment_ratio = 1
            start_date += datetime.timedelta(days=1)
        else:
            # If no data in either table, start from 5 years ago
            start_date = datetime.date.today() - datetime.timedelta(days=5*365)
            start_date_str = start_date.strftime('%Y-%m-%d')
        
        # Only fetch if start date is in the past
        today = datetime.date.today()
        if start_date > today:
            cursor.close()
            return 0
        
        # Fetch data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        
        # Determine end date based on number of days to fetch
        end_date = start_date + datetime.timedelta(days=num_days)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        data = ticker.history(start=start_date_str, end=end_date_str)
        
        if data.empty:
            cursor.close()
            return 0  # No new data available
        
        # Insert all fetched days
        inserted_count = 0
        for index, row in data.iterrows():
            # Convert index to date object
            date = index.date() if hasattr(index, 'date') else index.to_pydatetime().date()
            
            # Skip if date is in the future
            if date > today:
                continue
                
            open_price = float(row["Open"]) * adjustment_ratio
            high_price = float(row["High"]) * adjustment_ratio
            low_price = float(row["Low"]) * adjustment_ratio
            close_price = float(row["Close"]) * adjustment_ratio
            volume = int(row["Volume"]) / adjustment_ratio
            
            query = '''
                INSERT INTO DailyStockInfo (symbol, timestamp, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, timestamp) 
                DO UPDATE SET open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume
            '''
            cursor.execute(query, (symbol, date, open_price, high_price, low_price, close_price, volume))
            inserted_count += 1
        
        self.conn.commit()
        cursor.close()
        return inserted_count

    def fetch_and_store_all_stocks_daily_info(self, num_days=1):

        cursor = self.conn.cursor()
        
        # Get all stock symbols
        query = '''
            SELECT symbol FROM Stocks;
        '''
        cursor.execute(query)
        symbols = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        results = {}
        for symbol in symbols:
            try:
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                print(f"Fetching data for {symbol}...")
                inserted_count = self.fetch_and_store_daily_info_yahoo(symbol, num_days)
                if inserted_count:
                    results[symbol] = inserted_count
                    print(f"✅ Successfully updated {inserted_count} days for {symbol}")
                else:
                    results[symbol] = 0
                    print(f"ℹ️ No new data available for {symbol}")
            except Exception as e:
                print(f"❌ Error fetching data for {symbol}: {e}")
                results[symbol] = None
        
        return results
    
    def fetch_and_store_spy_info_between_dates(self, start_date, end_date):

        cursor = self.conn.cursor()
        
        try:
            # Format dates for Yahoo Finance API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Fetch SPY data from Yahoo Finance
            ticker = yf.Ticker("SPY")
            data = ticker.history(start=start_date_str, end=end_date_str)
            
            if data.empty:
                cursor.close()
                return 0  # No data available
            
            # Insert all fetched days
            inserted_count = 0
            for index, row in data.iterrows():
                # Convert index to date object
                date = index.date() if hasattr(index, 'date') else index.to_pydatetime().date()
                
                open_price = float(row["Open"])
                high_price = float(row["High"])
                low_price = float(row["Low"])
                close_price = float(row["Close"])
                volume = int(row["Volume"])
                
                # First, ensure SPY exists in the Stocks table
                ensure_spy_query = '''
                    INSERT INTO Stocks (symbol)
                    VALUES ('SPY')
                    ON CONFLICT (symbol) DO NOTHING;
                '''
                cursor.execute(ensure_spy_query)
                
                # Insert into DailyStockInfo
                query = '''
                    INSERT INTO DailyStockInfo (symbol, timestamp, open, high, low, close, volume)
                    VALUES ('SPY', %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, timestamp) 
                    DO UPDATE SET open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                close = EXCLUDED.close,
                                volume = EXCLUDED.volume;
                '''
                cursor.execute(query, (date, open_price, high_price, low_price, close_price, volume))
                inserted_count += 1
            
            self.conn.commit()
            cursor.close()
            return inserted_count
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error fetching SPY data: {e}")
            cursor.close()
            return None

    def view_stock_info(self, symbol, period='all', graph=False):

        cursor = self.conn.cursor()
        
        # Calculate the start date based on period
        # Get the most recent date from DailyStockInfo
        recent_date_query = '''
            SELECT MAX(timestamp) 
            FROM DailyStockInfo
            WHERE symbol = %s;
        '''
        cursor.execute(recent_date_query, (symbol,))
        latest_date = cursor.fetchone()[0]
        
        # If no data in DailyStockInfo, get most recent date from StocksHistory
        if not latest_date:
            history_date_query = '''
                SELECT MAX(timestamp) 
                FROM StocksHistory
                WHERE symbol = %s;
            '''
            cursor.execute(history_date_query, (symbol,))
            latest_date = cursor.fetchone()[0]

        if period == '5d':
            start_date = latest_date - datetime.timedelta(days=5)
        elif period == '1mo':
            start_date = latest_date - datetime.timedelta(days=30)
        elif period == '6mo':
            start_date = latest_date - datetime.timedelta(days=180)
        elif period == '1y':
            start_date = latest_date - datetime.timedelta(days=365)
        elif period == '5y':
            start_date = latest_date - datetime.timedelta(days=5*365)
        elif period == 'all':
            start_date = datetime.date(1900, 1, 1)
        else:
            cursor.close()
            return None
        
        query = '''
            SELECT timestamp, open, high, low, close, volume
            FROM StocksHistory
            WHERE symbol = %s AND timestamp >= %s
            UNION ALL
            SELECT timestamp, open, high, low, close, volume
            FROM DailyStockInfo
            WHERE symbol = %s AND timestamp >= %s
            ORDER BY timestamp ASC;
        '''
        cursor.execute(query, (symbol, start_date, symbol, start_date))
        data = cursor.fetchall()
        cursor.close()
        return data

    def display_stock_chart(self, symbol, period='all'):
        
        # Get stock data
        stock_data = self.view_stock_info(symbol, period)
        
        if not stock_data:
            print(f"No data available for {symbol}")
            return
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(stock_data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # Get period name for title
        period_names = {
            '5d': '5 Days', 
            '1mo': '1 Month', 
            '6mo': '6 Months', 
            '1y': '1 Year', 
            '5y': '5 Years', 
            'all': 'All Time'
        }
        period_name = period_names.get(period, 'Custom Period')
        
        mpf.plot(
            df,
            type='candle',
            title=f'{symbol} - {period_name}',
            ylabel='Price',
            volume=True,
            style='yahoo',
            figsize=(12, 8)
        )

        return df 

    def predict_stock_price(self, symbol: str, days_to_predict: int = 30) -> Tuple[List[Dict], float]:

        cursor = self.conn.cursor()
        
        # Get historical data
        data = self.view_stock_info(symbol, 'all')
        if not data:
            cursor.close()
            return [], 0.0
            
        # Convert to list of dicts
        historical_data = [{
            'timestamp': row[0].strftime('%Y-%m-%d'),
            'close': float(row[4])
        } for row in data]
        
        cursor.close()
        
        # Use prediction model
        from models.prediction_model import StockPredictionModel
        model = StockPredictionModel()
        return model.predict_future_prices(historical_data, days_to_predict) 