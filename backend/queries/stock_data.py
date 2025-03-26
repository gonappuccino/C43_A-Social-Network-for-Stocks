import psycopg2
import yfinance as yf
import datetime
import time
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from queries.utils import decimal_to_float as d2f

class StockData:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='postgres',
        user='postgres',
        password='2357'
    )

    def fetch_and_store_daily_info_yahoo(self, symbol, num_days=1):
        """
        Fetch stock info for 'symbol' from Yahoo Finance starting from the day after
        the most recent day recorded in the database, and insert/update it in the DailyStockInfo table.
        
        Args:
            symbol: The stock symbol to fetch data for
            num_days: Number of days to fetch (default: 1)
            
        Returns:
            Number of days inserted/updated, or None if no data
        """
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
        
        # Calculate the start date (day after the most recent date)
        if latest_date:
            start_date = latest_date + datetime.timedelta(days=1)
            # Format for Yahoo Finance API
            start_date_str = start_date.strftime('%Y-%m-%d')
        else:
            # If no data in either table, start from 5 years ago
            start_date = datetime.date.today() - datetime.timedelta(days=5*365)
            start_date_str = start_date.strftime('%Y-%m-%d')
        
        # Only fetch if start date is in the past
        today = datetime.date.today()
        if start_date > today:
            cursor.close()
            return 0  # Already up to date
        
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
                
            open_price = float(row["Open"])
            high_price = float(row["High"])
            low_price = float(row["Low"])
            close_price = float(row["Close"])
            volume = int(row["Volume"])
            
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
        """
        Fetch and store daily info for all stocks in the Stocks table.
        
        Args:
            num_days: Number of days to fetch for each stock (default: 1)
            
        Returns:
            Dictionary mapping symbols to number of days inserted/updated
        """
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

    def view_stock_info(self, symbol, period='all', graph=False):
        """
        Return merged historical data from StocksHistory plus any daily data
        from DailyStockInfo for the specified symbol, ordered by date descending.
        
        Args:
            symbol: The stock symbol to query
            period: Time period to filter data ('5d', '1mo', '6mo', '1y', '5y', 'all')
        """
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
        """
        Display a candlestick chart for the given stock symbol.
        
        Args:
            symbol: The stock symbol to chart
            period: Time period to display ('5d', '1mo', '6mo', '1y', '5y', 'all')
        """
        
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