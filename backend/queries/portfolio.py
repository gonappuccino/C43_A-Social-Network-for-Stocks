import psycopg2
from queries.utils import decimal_to_float as d2f
import datetime
import json
from typing import Optional, Dict

class Portfolio:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='postgres',
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
            RETURNING portfolio_entry_id, num_shares;
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
        """
        Decrease shares without dropping below zero.
        If resulting shares == 0, remove the record.
        """
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
                RETURNING portfolio_entry_id;
            '''
            cursor.execute(delete_query, (portfolio_id, symbol))
            result = cursor.fetchone()
        else:
            # Update the row to reflect new share count
            update_query = '''
                UPDATE PortfolioStocks
                   SET num_shares = num_shares - %s
                 WHERE portfolio_id = %s AND symbol = %s
                RETURNING portfolio_entry_id, num_shares;
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
        """
        View all transactions for a given portfolio.
        """
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
        """
        Returns the total current market value of the given portfolio, 
        including its cash balance and the latest stock prices.
        """
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
            SELECT COALESCE(SUM(ps.num_shares * sh.close), 0)
              FROM PortfolioStocks ps
              JOIN (
                SELECT symbol, MAX(timestamp) AS max_time
                  FROM (SELECT symbol, timestamp FROM StocksHistory 
                          UNION 
                        SELECT symbol, timestamp FROM DailyStockInfo) combined
                 GROUP BY symbol
              ) AS latest ON ps.symbol = latest.symbol
              JOIN (SELECT symbol, timestamp, close FROM StocksHistory 
                      UNION 
                    SELECT symbol, timestamp, close FROM DailyStockInfo) sh 
                ON sh.symbol = ps.symbol
               AND sh.timestamp = latest.max_time
             WHERE ps.portfolio_id = %s
        '''
        cursor.execute(value_query, (portfolio_id,))
        result = cursor.fetchone()
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
        """
        Return all portfolios owned by the specified user.
        """
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

    def compute_portfolio_analytics(self, user_id: int, portfolio_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[Dict]:
        """
        Compute portfolio analytics including coefficient of variation, Beta, and correlation/covariance matrices.
        Uses caching to improve performance for repeated queries.
        
        Args:
            user_id: The ID of the user requesting analytics
            portfolio_id: The ID of the portfolio to analyze
            start_date: Optional start date for analysis (YYYY-MM-DD)
            end_date: Optional end date for analysis (YYYY-MM-DD)
            
        Returns:
            Dictionary containing analytics results or None if error occurs
        """
        try:
            with self.conn.cursor() as cursor:
                # Check if user has access to portfolio
                cursor.execute("""
                    SELECT 1 FROM Portfolios 
                    WHERE portfolio_id = %s AND user_id = %s
                """, (portfolio_id, user_id))
                if not cursor.fetchone():
                    return None

                # If no dates provided, use entire history
                if not start_date or not end_date:
                    cursor.execute("""
                        SELECT MIN(timestamp), MAX(timestamp) 
                        FROM StocksHistory
                    """)
                    min_date, max_date = cursor.fetchone()
                    start_date = min_date.strftime('%Y-%m-%d')
                    end_date = max_date.strftime('%Y-%m-%d')

                # Check cache first
                cursor.execute("""
                    SELECT analytics_data, last_updated 
                    FROM PortfolioAnalyticsCache
                    WHERE portfolio_id = %s 
                    AND start_date = %s 
                    AND end_date = %s
                """, (portfolio_id, start_date, end_date))
                
                cached_result = cursor.fetchone()
                if cached_result:
                    return cached_result[0]

                # If not in cache, compute analytics
                # NOTE: Covariance computed with E(XY) - E(X)E(Y)
                # NOTE: when portfolio has only 1 stock, coefficient of variation is undefined, we use NULLIF to return None
                analytics_query = """
                    WITH daily_returns AS (
                        SELECT 
                            sh.symbol,
                            sh.timestamp,
                            (sh.close - LAG(sh.close) OVER (PARTITION BY sh.symbol ORDER BY sh.timestamp)) / 
                            LAG(sh.close) OVER (PARTITION BY sh.symbol ORDER BY sh.timestamp) as daily_return
                        FROM (
                            SELECT symbol, timestamp, close FROM StocksHistory
                            UNION ALL
                            SELECT symbol, timestamp, close FROM DailyStockInfo
                        ) sh
                        WHERE sh.timestamp BETWEEN %s AND %s
                    ),
                    spy_returns AS (
                        SELECT 
                            timestamp,
                            (close - LAG(close) OVER (ORDER BY timestamp)) / 
                            LAG(close) OVER (ORDER BY timestamp) as daily_return
                        FROM (
                            SELECT timestamp, close FROM StocksHistory WHERE symbol = 'SPY'
                            UNION ALL
                            SELECT timestamp, close FROM DailyStockInfo WHERE symbol = 'SPY'
                        ) spy
                        WHERE timestamp BETWEEN %s AND %s
                    ),
                    stock_stats AS (
                        SELECT 
                            dr.symbol,
                            AVG(dr.daily_return) as mean_return,
                            STDDEV(dr.daily_return) as std_dev,
                            AVG(dr.daily_return * sr.daily_return) - 
                            AVG(dr.daily_return) * AVG(sr.daily_return) as cov_with_spy,
                            VARIANCE(sr.daily_return) as spy_variance
                        FROM daily_returns dr
                        JOIN spy_returns sr ON dr.timestamp = sr.timestamp
                        GROUP BY dr.symbol
                    ),
                    correlation_matrix AS (
                        SELECT 
                            dr1.symbol as symbol1,
                            dr2.symbol as symbol2,
                            (AVG(dr1.daily_return * dr2.daily_return) - 
                             AVG(dr1.daily_return) * AVG(dr2.daily_return)) / 
                            (STDDEV(dr1.daily_return) * STDDEV(dr2.daily_return)) as correlation
                        FROM daily_returns dr1
                        JOIN daily_returns dr2 ON dr1.timestamp = dr2.timestamp
                        WHERE dr1.symbol < dr2.symbol
                        GROUP BY dr1.symbol, dr2.symbol
                    ),
                    covariance_matrix AS (
                        SELECT 
                            dr1.symbol as symbol1,
                            dr2.symbol as symbol2,
                            AVG(dr1.daily_return * dr2.daily_return) - 
                            AVG(dr1.daily_return) * AVG(dr2.daily_return) as covariance
                        FROM daily_returns dr1
                        JOIN daily_returns dr2 ON dr1.timestamp = dr2.timestamp
                        GROUP BY dr1.symbol, dr2.symbol
                    )
                    SELECT 
                        ss.symbol,
                        ss.std_dev / NULLIF(ABS(ss.mean_return), 0) as coefficient_of_variation,
                        ss.cov_with_spy / NULLIF(ss.spy_variance, 0) as beta,
                        cm.symbol2 as corr_symbol2,
                        cm.correlation,
                        covm.symbol2 as cov_symbol2,
                        covm.covariance
                    FROM stock_stats ss
                    LEFT JOIN correlation_matrix cm ON ss.symbol = cm.symbol1
                    LEFT JOIN covariance_matrix covm ON ss.symbol = covm.symbol1
                    ORDER BY ss.symbol;
                """
                
                cursor.execute(analytics_query, (start_date, end_date, start_date, end_date))
                results = cursor.fetchall()
                
                if not results:
                    return None

                # Process results into structured format
                stock_analytics = []
                correlation_matrix = {}
                covariance_matrix = {}
                
                for row in results:
                    symbol = row[0]
                    cv = float(row[1]) if row[1] is not None else None
                    beta = float(row[2]) if row[2] is not None else None
                    
                    stock_analytics.append({
                        'symbol': symbol,
                        'coefficient_of_variation': cv,
                        'beta': beta
                    })
                    
                    if row[3] and row[4]:  # Correlation data
                        if symbol not in correlation_matrix:
                            correlation_matrix[symbol] = {}
                        correlation_matrix[symbol][row[3]] = float(row[4])
                        if row[3] not in correlation_matrix:
                            correlation_matrix[row[3]] = {}
                        correlation_matrix[row[3]][symbol] = float(row[4])
                    
                    if row[5] and row[6]:  # Covariance data
                        if symbol not in covariance_matrix:
                            covariance_matrix[symbol] = {}
                        covariance_matrix[symbol][row[5]] = float(row[6])
                        if row[5] not in covariance_matrix:
                            covariance_matrix[row[5]] = {}
                        covariance_matrix[row[5]][symbol] = float(row[6])

                analytics_result = {
                    'stock_analytics': stock_analytics,
                    'correlation_matrix': correlation_matrix,
                    'covariance_matrix': covariance_matrix,
                    'date_range': {
                        'start': start_date,
                        'end': end_date
                    }
                }

                # Cache the results
                cursor.execute("""
                    INSERT INTO PortfolioAnalyticsCache 
                        (portfolio_id, start_date, end_date, analytics_data)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (portfolio_id, start_date, end_date) 
                    DO UPDATE SET 
                        analytics_data = EXCLUDED.analytics_data,
                        last_updated = CURRENT_TIMESTAMP
                """, (portfolio_id, start_date, end_date, json.dumps(analytics_result)))

                return analytics_result

        except Exception as e:
            print(f"Error computing portfolio analytics: {e}")
            return None 

    def view_portfolio_history(self, user_id, portfolio_id, period='all'):
        """
        Return the historical value of a portfolio over time, calculated using the current holdings.
        
        Args:
            user_id: The ID of the user requesting the history
            portfolio_id: The ID of the portfolio to analyze
            period: Time period to filter data ('5d', '1mo', '6mo', '1y', '5y', 'all')
            
        Returns:
            List of tuples containing (timestamp, total_value) ordered by timestamp ascending
        """
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
            SELECT MAX(timestamp) 
            FROM (
                SELECT timestamp FROM DailyStockInfo
                UNION
                SELECT timestamp FROM StocksHistory
            ) all_dates;
        '''
        cursor.execute(recent_date_query)
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
                WHERE timestamp >= %s
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
        
        cursor.execute(history_query, (start_date, portfolio_id, cash_balance))
        history = cursor.fetchall()
        cursor.close()
        return history 