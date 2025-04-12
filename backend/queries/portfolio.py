import psycopg2
from queries.utils import decimal_to_float as d2f
import datetime
import json
from typing import Optional, Dict, Tuple, List

class Portfolio:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='template1',
        user='postgres',
        password='2357'
    )

    def create_portfolio(self, user_id, portfolio_name, initial_cash=0):
        try:
            user_id = int(user_id)  # Ensure integer conversion
            initial_cash = float(initial_cash)  # Ensure float conversion
            
            cursor = self.conn.cursor()
            query = '''
                INSERT INTO Portfolios (portfolio_name, user_id, cash_balance)
                VALUES (%s, %s, %s)
                RETURNING portfolio_id;
            '''
            cursor.execute(query, (portfolio_name, user_id, initial_cash))
            portfolio_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            return portfolio_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error in create_portfolio: {e}")
            raise e
        
    def delete_portfolio(self, portfolio_id, user_id):
        """
        Delete a portfolio by its ID, but only if the specified user is the owner.
        """
        cursor = self.conn.cursor()
        
        # Proceed with deletion
        delete_query = '''
            DELETE FROM Portfolios
            WHERE portfolio_id = %s AND user_id = %s
            RETURNING portfolio_id;
        '''
        cursor.execute(delete_query, (portfolio_id, user_id))
        deleted_id = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return deleted_id

    def update_cash_balance(self, user_id, portfolio_id, amount, record_transaction=True):
        cursor = self.conn.cursor()
        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        # Above query also checks if the portfolio exists
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None

        # If amount is negative, check if the portfolio has enough cash to withdraw
        if amount < 0:
            query = '''
                SELECT cash_balance
                  FROM Portfolios
                 WHERE portfolio_id = %s
            '''
            cursor.execute(query, (portfolio_id,))
            current_balance = d2f(cursor.fetchone()[0])
            if current_balance + amount < 0:
                cursor.close()
                return None
            
        query = '''
            UPDATE Portfolios
            SET cash_balance = cash_balance + %s
            WHERE portfolio_id = %s
            RETURNING cash_balance;
        '''
        cursor.execute(query, (amount, portfolio_id))
        updated_balance = cursor.fetchone()[0]

        if not record_transaction:
            self.conn.commit()
            cursor.close()
            return updated_balance
        
        # record transaction
        transaction_query = '''
            INSERT INTO PortfolioTransactions (portfolio_id, symbol, transaction_type, shares, price, cash_change)
            VALUES (%s, NULL, 'CASH', 0, 0, %s)
        '''
        cursor.execute(transaction_query, (portfolio_id, amount))

        self.conn.commit()
        cursor.close()
        return updated_balance
    
    def get_cash_balance(self, portfolio_id, user_id):
        cursor = self.conn.cursor()
        query = '''
            SELECT cash_balance
              FROM Portfolios
             WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(query, (portfolio_id, user_id))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            return None
        cash_balance = d2f(result[0])
        cursor.close()
        return cash_balance

    def buy_stock_shares(self, user_id, portfolio_id, symbol, num_shares):
        cursor = self.conn.cursor()

        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None

        # Get the latest price per share from StockHistory 
        price_query = '''
            (SELECT close, timestamp
              FROM DailyStockInfo
             WHERE symbol = %s
            UNION
            SELECT close, timestamp
              FROM StocksHistory
             WHERE symbol = %s)
            ORDER BY timestamp DESC
            LIMIT 1;
        '''
        cursor.execute(price_query, (symbol, symbol))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            return None  # No price data available
        price_per_share = d2f(result[0])
        
        # Calculate the total cost and check if the portfolio has enough cash
        total_cost = num_shares * price_per_share

        result = self.update_cash_balance(user_id, portfolio_id, -total_cost, record_transaction=False)
        if not result:
            cursor.close()
            return None

        query = '''
            INSERT INTO PortfolioStocks (portfolio_id, symbol, num_shares)
            VALUES (%s, %s, %s)
            ON CONFLICT (portfolio_id, symbol)
            DO UPDATE SET num_shares = PortfolioStocks.num_shares + EXCLUDED.num_shares
            RETURNING num_shares;
        '''
        cursor.execute(query, (portfolio_id, symbol, num_shares))
        result = cursor.fetchone()

        # Record the transaction
        transaction_query = '''
            INSERT INTO PortfolioTransactions (portfolio_id, symbol, transaction_type, shares, price, cash_change)
            VALUES (%s, %s, 'BUY', %s, %s, %s)
        '''
        cursor.execute(transaction_query, (portfolio_id, symbol, num_shares, price_per_share, -total_cost))

        self.conn.commit()
        cursor.close()
        return result
    
    def sell_stock_shares(self, user_id, portfolio_id, symbol, num_shares):
        cursor = self.conn.cursor()

        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None

        
        # Check current shares
        check_query = '''
            SELECT num_shares
              FROM PortfolioStocks
             WHERE portfolio_id = %s AND symbol = %s
        '''
        cursor.execute(check_query, (portfolio_id, symbol))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            return None  # No record to remove shares from

        current_shares = d2f(existing[0])
        if current_shares < num_shares:
            # Not allowed to remove more than owned
            cursor.close()
            return None
        elif current_shares == num_shares:
            # Remove the stock row entirely
            delete_query = '''
                DELETE FROM PortfolioStocks
                 WHERE portfolio_id = %s AND symbol = %s
                RETURNING num_shares;
            '''
            cursor.execute(delete_query, (portfolio_id, symbol))
            result = cursor.fetchone()
        else:
            # Update the row to reflect new share count
            update_query = '''
                UPDATE PortfolioStocks
                   SET num_shares = num_shares - %s
                 WHERE portfolio_id = %s AND symbol = %s
                RETURNING num_shares;
            '''
            cursor.execute(update_query, (num_shares, portfolio_id, symbol))
            result = cursor.fetchone()

        # Get the latest price per share from StockHistory
        price_query = '''
            (SELECT close, timestamp
              FROM DailyStockInfo
             WHERE symbol = %s
            UNION
            SELECT close, timestamp
              FROM StocksHistory
             WHERE symbol = %s)
            ORDER BY timestamp DESC
            LIMIT 1;
        '''
        cursor.execute(price_query, (symbol, symbol))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            return None
        price_per_share = d2f(result[0])
        if not price_per_share:
            cursor.close()
            return None  # No price data available
        
        # Calculate the total revenue
        total_revenue = num_shares * price_per_share

        # Update the cash balance
        self.update_cash_balance(user_id, portfolio_id, total_revenue, record_transaction=False)

        # Record the transaction
        transaction_query = '''
            INSERT INTO PortfolioTransactions (portfolio_id, symbol, transaction_type, shares, price, cash_change)
            VALUES (%s, %s, 'SELL', %s, %s, %s)
        '''
        cursor.execute(transaction_query, (portfolio_id, symbol, num_shares, price_per_share, total_revenue))

        self.conn.commit()
        cursor.close()
        return result

    def view_portfolio(self, user_id, portfolio_id):
        cursor = self.conn.cursor()
        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None
        query = '''
            SELECT p.portfolio_id, p.cash_balance, ps.symbol, ps.num_shares
            FROM Portfolios p
            LEFT JOIN PortfolioStocks ps ON p.portfolio_id = ps.portfolio_id
            WHERE p.portfolio_id = %s;
        '''
        cursor.execute(query, (portfolio_id,))
        portfolio_data = cursor.fetchall()
        cursor.close()
        return portfolio_data

    def view_portfolio_transactions(self, user_id, portfolio_id):
        cursor = self.conn.cursor()
        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None

        query = '''
            SELECT transaction_id, portfolio_id, symbol, transaction_type, shares, price, cash_change, transaction_time
              FROM PortfolioTransactions
             WHERE portfolio_id = %s
             ORDER BY transaction_time DESC;
        '''
        cursor.execute(query, (portfolio_id,))
        transactions = cursor.fetchall()
        cursor.close()
        return transactions

    def compute_portfolio_value(self, user_id, portfolio_id):
        cursor = self.conn.cursor()
        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None
        # cash balance
        cash_query = '''
            SELECT cash_balance
              FROM Portfolios
             WHERE portfolio_id = %s
        '''
        cursor.execute(cash_query, (portfolio_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return 0.0  # Portfolio doesn't exist
        cash_balance = float(row[0])

        # stock value
        # latest close stock price for each stock in the portfolio multiplied by num shares
        # coalesce to 0 if no shares
        value_query = '''
            WITH latest_prices AS (
                SELECT 
                    symbol,
                    MAX(timestamp) as max_time
                FROM (
                    SELECT symbol, timestamp FROM StocksHistory
                    UNION ALL
                    SELECT symbol, timestamp FROM DailyStockInfo
                ) combined
                GROUP BY symbol
            ),
            current_prices AS (
                SELECT 
                    sh.symbol,
                    COALESCE(sh.close, dsi.close) as close_price
                FROM latest_prices lp
                LEFT JOIN StocksHistory sh ON sh.symbol = lp.symbol AND sh.timestamp = lp.max_time
                LEFT JOIN DailyStockInfo dsi ON dsi.symbol = lp.symbol AND dsi.timestamp = lp.max_time
            )
            SELECT COALESCE(SUM(ps.num_shares * cp.close_price), 0)
            FROM PortfolioStocks ps
            JOIN current_prices cp ON ps.symbol = cp.symbol
            WHERE ps.portfolio_id = %s;
        '''
        # import time
        # start_time = time.time()
        cursor.execute(value_query, (portfolio_id,))
        result = cursor.fetchone()
        # end_time = time.time()
        # print(f"Time taken to execute value_query: {end_time - start_time} seconds")
        if not result:
            cursor.close()
            return None
        
        stock_value = d2f(result[0])
        if not stock_value:
            cursor.close()
            return cash_balance

        total_value = float(cash_balance) + float(stock_value)

        cursor.close()
        return total_value

    def view_user_portfolios(self, user_id):
        cursor = self.conn.cursor()
        query = '''
            SELECT p.portfolio_id, p.portfolio_name, p.cash_balance, 
                COALESCE(SUM(ps.num_shares), 0) AS total_stocks,
                p.created_at
            FROM Portfolios p
            LEFT JOIN PortfolioStocks ps ON p.portfolio_id = ps.portfolio_id
            WHERE p.user_id = %s
            GROUP BY p.portfolio_id, p.cash_balance, p.created_at
            ORDER BY p.created_at DESC;
        '''
        cursor.execute(query, (user_id,))
        portfolios = cursor.fetchall()
        cursor.close()
        return portfolios 

    def compute_portfolio_analytics(self, user_id, portfolio_id, start_date=None, end_date=None):

        cursor = self.conn.cursor()
        
        # Check if user has access to portfolio
        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None
        
        if not end_date and not start_date:
            recent_date_query = '''
                SELECT MIN(max_ts)
                FROM (
                    SELECT ps.symbol, MAX(combined.timestamp) as max_ts
                    FROM PortfolioStocks ps
                    JOIN (
                        SELECT symbol, timestamp FROM DailyStockInfo
                        UNION ALL
                        SELECT symbol, timestamp FROM StocksHistory
                    ) combined ON ps.symbol = combined.symbol
                    WHERE ps.portfolio_id = %s
                    GROUP BY ps.symbol
                ) AS symbol_max_dates;
            '''
            cursor.execute(recent_date_query, (portfolio_id,))
            latest_date = cursor.fetchone()[0]
            if not latest_date:
                cursor.close()
                return None
            
            end_date = latest_date
            earliest_date_query = '''
                SELECT MIN(timestamp)
                FROM (
                    SELECT symbol, timestamp FROM DailyStockInfo
                    UNION ALL
                    SELECT symbol, timestamp FROM StocksHistory
                ) combined
            '''
            cursor.execute(earliest_date_query, (portfolio_id,))
            start_date = cursor.fetchone()[0]
            
        # Get all stocks in portfolio
        stocks_query = '''
            SELECT DISTINCT symbol, num_shares
            FROM PortfolioStocks
            WHERE portfolio_id = %s
        '''
        cursor.execute(stocks_query, (portfolio_id,))
        portfolio_stocks = cursor.fetchall()
        
        if not portfolio_stocks:
            print("No stocks in portfolio")
            cursor.close()
            return None
            
        # Check if SPY data is available for the date range
        # NOTE: Currently all spy data is stored in DailyStockInfo even though the dates may
        # be in the range of what is in StocksHistory
        spy_check_query = '''
            SELECT COUNT(*)
            FROM (
                SELECT timestamp
                FROM DailyStockInfo
                WHERE symbol = 'SPY' AND timestamp BETWEEN %s AND %s
            ) spy_data
        '''
        cursor.execute(spy_check_query, (start_date, end_date))
        spy_count = cursor.fetchone()[0]
        
        # If SPY data is missing, fetch it
        if spy_count < 10:  # Require at least 10 data points for meaningful analysis
            from queries.stock_data import StockData
            stock_data = StockData()
            fetched_count = stock_data.fetch_and_store_spy_info_between_dates(start_date, end_date)
            if fetched_count is None or fetched_count == 0:
                cursor.close()
                print("Could not fetch SPY data")
                return None  # Could not fetch SPY data
            

        # Calculate daily returns, CV, and Beta for each stock
        analytics_query = '''
            WITH daily_returns AS (
                SELECT 
                    symbol,
                    timestamp,
                    (close - LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp)) / LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp) as daily_return
                FROM (
                    (SELECT symbol, timestamp, close
                    FROM StocksHistory
                    WHERE symbol IN %s AND timestamp >= %s AND timestamp <= %s)
                    UNION ALL
                    (SELECT symbol, timestamp, close
                    FROM DailyStockInfo
                    WHERE symbol IN %s AND timestamp >= %s AND timestamp <= %s)
                ) combined
            ),
            spy_returns AS (
                SELECT 
                    timestamp,
                    (close - LAG(close) OVER (ORDER BY timestamp)) / LAG(close) OVER (ORDER BY timestamp) as spy_return
                FROM (
                    SELECT timestamp, close
                    FROM DailyStockInfo
                    WHERE symbol = 'SPY' AND timestamp >= %s AND timestamp <= %s
                ) spy_data
            ),
            stock_stats AS (
                SELECT 
                    dr.symbol,
                    AVG(dr.daily_return) as mean_return,
                    STDDEV(dr.daily_return) as std_return,
                    (AVG(dr.daily_return * sr.spy_return) - AVG(dr.daily_return) * AVG(sr.spy_return)) as cov_with_spy,
                    VARIANCE(sr.spy_return) as spy_variance
                FROM daily_returns dr
                JOIN spy_returns sr ON dr.timestamp = sr.timestamp
                WHERE dr.daily_return IS NOT NULL AND sr.spy_return IS NOT NULL
                GROUP BY dr.symbol
            ),
            correlation_matrix AS (
                SELECT 
                    a.symbol as symbol1,
                    b.symbol as symbol2,
                    (AVG(a.daily_return * b.daily_return) - AVG(a.daily_return) * AVG(b.daily_return)) / 
                    (STDDEV(a.daily_return) * STDDEV(b.daily_return)) as correlation
                FROM daily_returns a
                JOIN daily_returns b ON a.timestamp = b.timestamp
                GROUP BY a.symbol, b.symbol
            ),
            covariance_matrix AS (
                SELECT 
                    a.symbol as symbol1,
                    b.symbol as symbol2,
                    (AVG(a.daily_return * b.daily_return) - AVG(a.daily_return) * AVG(b.daily_return)) as covariance
                FROM daily_returns a
                JOIN daily_returns b ON a.timestamp = b.timestamp
                GROUP BY a.symbol, b.symbol
            )
            SELECT 
                ss.symbol,
                ss.mean_return,
                ss.std_return,
                CASE 
                    WHEN ss.mean_return = 0 THEN 0 
                    ELSE ss.std_return / ss.mean_return 
                END as coefficient_of_variation,
                CASE 
                    WHEN ss.spy_variance = 0 THEN 0 
                    ELSE ss.cov_with_spy / ss.spy_variance 
                END as beta,
                cm.symbol2,
                cm.correlation,
                covm.symbol2 as cov_symbol2,
                covm.covariance
            FROM stock_stats ss
            LEFT JOIN correlation_matrix cm ON ss.symbol = cm.symbol1
            LEFT JOIN covariance_matrix covm ON ss.symbol = covm.symbol1
            ORDER BY ss.symbol, cm.symbol2, covm.symbol2;
        '''
        
        # Prepare parameters for the query
        symbols = tuple(stock[0] for stock in portfolio_stocks)
        params = (symbols, start_date, end_date, symbols, start_date, end_date,
                 start_date, end_date)
        
        # import time
        # start_time = time.time()    
        cursor.execute(analytics_query, params)
        analytics_data = cursor.fetchall()
        # end_time = time.time()  
        # print(f"Time taken to execute analytics_query: {end_time - start_time} seconds")
        
        if not analytics_data:
            cursor.close()
            print("No analytics data")
            return None
            
        stock_analytics = []
        correlation_matrix = {}
        covariance_matrix = {}
        
        current_symbol = None
        for row in analytics_data:
            symbol = row[0]
            cv = float(row[3])
            beta = float(row[4])
            corr_symbol2 = row[5]
            correlation = float(row[6]) if row[6] is not None else 0
            cov_symbol2 = row[7]
            covariance = float(row[8]) if row[8] is not None else 0
            
            # Add stock analytics if we haven't seen this symbol before
            if symbol != current_symbol:
                current_symbol = symbol
                stock_analytics.append({
                    'symbol': symbol,
                    'shares': next(stock[1] for stock in portfolio_stocks if stock[0] == symbol),
                    'coefficient_of_variation': cv,
                    'beta': beta
                })
                correlation_matrix[symbol] = {symbol: 1.0}  # Self-correlation is always 1
                covariance_matrix[symbol] = {symbol: covariance}  # Self-covariance
            
            # Add correlation and covariance data if available
            if corr_symbol2 is not None:
                correlation_matrix[symbol][corr_symbol2] = correlation
                if corr_symbol2 not in correlation_matrix:
                    correlation_matrix[corr_symbol2] = {}
                correlation_matrix[corr_symbol2][symbol] = correlation
                correlation_matrix[corr_symbol2][corr_symbol2] = 1.0
            
            if cov_symbol2 is not None:
                covariance_matrix[symbol][cov_symbol2] = covariance
                if cov_symbol2 not in covariance_matrix:
                    covariance_matrix[cov_symbol2] = {}
                covariance_matrix[cov_symbol2][symbol] = covariance
                #covariance_matrix[cov_symbol2][cov_symbol2] = covariance
        
        cursor.close()
        return {
            'stock_analytics': stock_analytics,
            'correlation_matrix': correlation_matrix,
            'covariance_matrix': covariance_matrix
        } 

    def view_portfolio_history(self, user_id, portfolio_id, period='all'):
        cursor = self.conn.cursor()
        
        # Check if user has access to portfolio
        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        if not cursor.fetchone():
            cursor.close()
            return None
            
        # Get current portfolio holdings
        holdings_query = '''
            SELECT symbol, num_shares
            FROM PortfolioStocks
            WHERE portfolio_id = %s
        '''
        cursor.execute(holdings_query, (portfolio_id,))
        holdings = cursor.fetchall()
        
        if not holdings:
            cursor.close()
            return None
            
        # Get cash balance
        cash_balance = self.get_cash_balance(portfolio_id, user_id)
        if cash_balance is None:
            cursor.close()
            return None
            
        # Get the most recent date from DailyStockInfo or StocksHistory
        recent_date_query = '''
            SELECT MIN(max_ts)
            FROM (
                SELECT ps.symbol, MAX(combined.timestamp) as max_ts
                FROM PortfolioStocks ps
                JOIN (
                    SELECT symbol, timestamp FROM DailyStockInfo
                    UNION ALL
                    SELECT symbol, timestamp FROM StocksHistory
                ) combined ON ps.symbol = combined.symbol
                WHERE ps.portfolio_id = %s
                GROUP BY ps.symbol
            ) AS symbol_max_dates;
        '''
        cursor.execute(recent_date_query, (portfolio_id,))
        latest_date = cursor.fetchone()[0]
        
        if not latest_date:
            cursor.close()
            return None
            
        # Calculate the start date based on period
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
            
        # Get historical data for all stocks in the portfolio
        history_query = '''
            WITH portfolio_dates AS (
                SELECT DISTINCT timestamp
                FROM (
                    SELECT timestamp FROM StocksHistory
                    UNION
                    SELECT timestamp FROM DailyStockInfo
                ) all_dates
                WHERE timestamp >= %s AND timestamp <= %s
            ),
            stock_values AS (
                SELECT 
                    pd.timestamp,
                    ps.symbol,
                    ps.num_shares,
                    COALESCE(sh.close, dsi.close) as close_price
                FROM portfolio_dates pd
                CROSS JOIN (
                    SELECT symbol, num_shares
                    FROM PortfolioStocks
                    WHERE portfolio_id = %s
                ) ps
                LEFT JOIN StocksHistory sh ON sh.symbol = ps.symbol AND sh.timestamp = pd.timestamp
                LEFT JOIN DailyStockInfo dsi ON dsi.symbol = ps.symbol AND dsi.timestamp = pd.timestamp
            )
            SELECT 
                timestamp,
                SUM(num_shares * close_price) + %s as total_value
            FROM stock_values
            GROUP BY timestamp
            ORDER BY timestamp ASC;
        '''
        
        # import time
        # start_time = time.time()
        cursor.execute(history_query, (start_date, latest_date, portfolio_id, cash_balance))
        history = cursor.fetchall()
        # end_time = time.time()
        # print(f"Time taken to execute history_query: {end_time - start_time} seconds")
        cursor.close()
        return history 

    def predict_portfolio_value(self, user_id: int, portfolio_id: int, days_to_predict: int = 30) -> Tuple[List[Dict], float]:

        cursor = self.conn.cursor()
        
        # Check if user has access to portfolio
        is_owner_query = '''
            SELECT 1
                FROM Portfolios
                WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(is_owner_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return [], 0.0
        
        # Get cash balance
        cash_balance = self.get_cash_balance(portfolio_id, user_id)
        if cash_balance is None:
            cursor.close()
            return [], 0.0
            
        # Get the minimum of maximum dates for all stocks in the portfolio
        max_dates_query = '''
            SELECT MIN(max_ts)
            FROM (
                SELECT ps.symbol, MAX(combined.timestamp) as max_ts
                FROM PortfolioStocks ps
                JOIN (
                    SELECT symbol, timestamp FROM StocksHistory
                    UNION ALL
                    SELECT symbol, timestamp FROM DailyStockInfo
                ) combined ON ps.symbol = combined.symbol
                WHERE ps.portfolio_id = %s
                GROUP BY ps.symbol
            ) AS symbol_max_dates;
        '''
        cursor.execute(max_dates_query, (portfolio_id,))
        latest_date = cursor.fetchone()[0]
        
        if not latest_date:
            cursor.close()
            return [], 0.0
            
        # Get historical portfolio values up to the latest common date
        history_query = '''
            WITH portfolio_dates AS (
                SELECT DISTINCT timestamp
                FROM (
                    SELECT timestamp FROM StocksHistory
                    UNION
                    SELECT timestamp FROM DailyStockInfo
                ) all_dates
                WHERE timestamp <= %s
            ),
            stock_values AS (
                SELECT 
                    pd.timestamp,
                    ps.symbol,
                    ps.num_shares,
                    COALESCE(sh.close, dsi.close) as close_price
                FROM portfolio_dates pd
                CROSS JOIN (
                    SELECT symbol, num_shares
                    FROM PortfolioStocks
                    WHERE portfolio_id = %s
                ) ps
                LEFT JOIN StocksHistory sh ON sh.symbol = ps.symbol AND sh.timestamp = pd.timestamp
                LEFT JOIN DailyStockInfo dsi ON dsi.symbol = ps.symbol AND dsi.timestamp = pd.timestamp
            )
            SELECT 
                timestamp,
                SUM(num_shares * close_price) + %s as total_value
            FROM stock_values
            GROUP BY timestamp
            ORDER BY timestamp ASC;
        '''
        
        cursor.execute(history_query, (latest_date, portfolio_id, cash_balance))
        portfolio_data = [{'timestamp': row[0].strftime('%Y-%m-%d'), 'value': float(row[1])} 
                         for row in cursor.fetchall()]
        
        cursor.close()
        
        # Use prediction model
        from models.prediction_model import PortfolioPredictionModel
        model = PortfolioPredictionModel()
        return model.predict_portfolio_value(portfolio_data, days_to_predict) 