import psycopg2
from queries.utils import decimal_to_float as d2f
from queries.friends import Friends
import datetime
from typing import List, Dict, Tuple

class StockList:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='template1',
        user='postgres',
        password='2357'
    )
    friends = Friends()

    def ensure_connection(self):
        if self.conn.closed:
            self.conn = psycopg2.connect(
                host='34.130.75.185',
                database='template1',
                user='postgres',
                password='2357'
            )

    def create_stock_list(self, creator_id, list_name, is_public=False):
        self.ensure_connection()
        try:
            creator_id = int(creator_id)  # Ensure integer conversion
            is_public = bool(is_public)  # Ensure boolean conversion
            
            cursor = self.conn.cursor()
            # Insert the new list
            insert_list_query = '''
                INSERT INTO StockLists (list_name, creator_id, is_public)
                VALUES (%s, %s, %s)
                RETURNING stocklist_id;
            '''
            cursor.execute(insert_list_query, (list_name, creator_id, is_public))
            stocklist_id = cursor.fetchone()[0]

            # Add an access row for the owner
            insert_access_query = '''
                INSERT INTO StockListAccess (stocklist_id, user_id, access_role)
                VALUES (%s, %s, 'owner');
            '''
            cursor.execute(insert_access_query, (stocklist_id, creator_id))

            self.conn.commit()
            cursor.close()
            return stocklist_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error in create_stock_list: {e}")
            raise e
    
    def delete_stock_list(self, stocklist_id, user_id):

        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Check if the user is the creator or has 'owner' role
        check_owner_query = '''
            SELECT 1
            FROM StockLists sl
            LEFT JOIN StockListAccess sla ON sl.stocklist_id = sla.stocklist_id
            WHERE sl.stocklist_id = %s
            AND (sl.creator_id = %s OR (sla.user_id = %s AND sla.access_role = 'owner'))
        '''
        cursor.execute(check_owner_query, (stocklist_id, user_id, user_id))
        is_owner = cursor.fetchone()
        
        if not is_owner:
            cursor.close()
            return None  # User is not the owner
        
        # Proceed with deletion
        delete_query = '''
            DELETE FROM StockLists
            WHERE stocklist_id = %s
            RETURNING stocklist_id;
        '''
        cursor.execute(delete_query, (stocklist_id,))
        deleted_id = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return deleted_id
    
    def add_stock_to_list(self, user_id, stocklist_id, symbol, num_shares):

        self.ensure_connection()
        cursor = self.conn.cursor()

        try:
            # First check if the stock exists
            check_stock_query = '''
                SELECT 1 FROM DailyStockInfo WHERE symbol = %s
                UNION
                SELECT 1 FROM StocksHistory WHERE symbol = %s
                LIMIT 1;
            '''
            cursor.execute(check_stock_query, (symbol, symbol))
            if not cursor.fetchone():
                cursor.close()
                return None  # Stock does not exist

            is_owner_query = '''
                SELECT 1
                FROM StockLists sl
                WHERE sl.stocklist_id = %s AND sl.creator_id = %s
            '''
            cursor.execute(is_owner_query, (stocklist_id, user_id))
            is_owner = cursor.fetchone()
            if not is_owner:
                cursor.close()
                return None

            query = '''
                INSERT INTO StockListStocks (stocklist_id, symbol, num_shares)
                VALUES (%s, %s, %s)
                ON CONFLICT (stocklist_id, symbol)
                DO UPDATE SET num_shares = StockListStocks.num_shares + EXCLUDED.num_shares
                RETURNING num_shares;
            '''
            cursor.execute(query, (stocklist_id, symbol, num_shares))
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return result
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            print(f"Error in add_stock_to_list: {e}")
            return None

    def remove_stock_from_list(self, user_id, stocklist_id, symbol, num_shares):

        self.ensure_connection()
        cursor = self.conn.cursor()

        is_owner_query = '''
            SELECT 1
            FROM StockLists sl
            WHERE sl.stocklist_id = %s AND sl.creator_id = %s
        '''
        cursor.execute(is_owner_query, (stocklist_id, user_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None
        
        # Check current shares
        check_query = '''
            SELECT num_shares
              FROM StockListStocks
             WHERE stocklist_id = %s AND symbol = %s
        '''
        cursor.execute(check_query, (stocklist_id, symbol))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            return None

        current_shares = existing[0]
        if current_shares < num_shares:
            cursor.close()
            return None
        elif current_shares == num_shares:
            delete_query = '''
                DELETE FROM StockListStocks
                 WHERE stocklist_id = %s AND symbol = %s
                RETURNING num_shares;
            '''
            cursor.execute(delete_query, (stocklist_id, symbol))
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return result
        else:
            update_query = '''
                UPDATE StockListStocks
                   SET num_shares = num_shares - %s
                 WHERE stocklist_id = %s AND symbol = %s
                RETURNING num_shares;
            '''
            cursor.execute(update_query, (num_shares, stocklist_id, symbol))
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return result

    def view_stock_list(self, user_id, stocklist_id):
        accessible_stock_lists = self.view_accessible_stock_lists(user_id)
        if not any([lst[0] == stocklist_id for lst in accessible_stock_lists]):
            return None
        
        cursor = self.conn.cursor()
        query = '''
            SELECT sl.stocklist_id, sl.is_public, sl.creator_id,
                   sls.symbol, sls.num_shares
            FROM StockLists sl
            LEFT JOIN StockListStocks sls
            ON sl.stocklist_id = sls.stocklist_id
            WHERE sl.stocklist_id = %s;
        '''
        cursor.execute(query, (stocklist_id,))
        stocklist_data = cursor.fetchall()
        cursor.close()
        return stocklist_data

    def share_stock_list(self, stocklist_id, owner_id, friend_id):

        self.ensure_connection()
        cursor = self.conn.cursor()
        # Check if the caller actually owns this list or is in owner role
        check_owner_query = '''
            SELECT 1
              FROM StockLists
              WHERE stocklist_id = %s AND creator_id = %s;
        '''
        cursor.execute(check_owner_query, (stocklist_id, owner_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return -1  # Caller is not the owner.
        
        # Check if friend_id is actually a friend of owner_id
        friends_list = self.friends.view_friends(owner_id)
        friend_ids = [f[0] for f in friends_list]
        if friend_id not in friend_ids:
            cursor.close()
            return -2  # Friend is not a friend of the owner.

        # Insert or update an access row for the friend
        share_query = '''
            INSERT INTO StockListAccess (stocklist_id, user_id, access_role)
            VALUES (%s, %s, 'shared')
            ON CONFLICT (stocklist_id, user_id)
            DO UPDATE SET access_role = 'shared';
        '''
        cursor.execute(share_query, (stocklist_id, friend_id))

        self.conn.commit()
        cursor.close()
        return 1

    def unshare_stock_list(self, stocklist_id, owner_id, friend_id):

        self.ensure_connection()
        cursor = self.conn.cursor()
        # Check if the caller actually owns this list
        check_owner_query = '''
            SELECT 1
            FROM StockListAccess
            WHERE stocklist_id = %s AND user_id = %s AND access_role = 'owner';
        '''
        cursor.execute(check_owner_query, (stocklist_id, owner_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None  # Caller is not the owner
        
        # Remove the friend's access
        delete_access_query = '''
            DELETE FROM StockListAccess
            WHERE stocklist_id = %s AND user_id = %s AND access_role = 'shared'
            RETURNING stocklist_id;
        '''
        cursor.execute(delete_access_query, (stocklist_id, friend_id))
        result = cursor.fetchone()
        
        self.conn.commit()
        cursor.close()
        return result is not None

    def view_accessible_stock_lists(self, user_id):

        self.ensure_connection()
        cursor = self.conn.cursor()
        query = '''
            SELECT DISTINCT sl.stocklist_id,
                            sl.list_name,
                            sl.creator_id,
                            u.username AS creator_name,
                            sl.is_public,
                            CASE WHEN sla.access_role = 'owner' THEN 'private'
                                 WHEN sla.access_role = 'shared' THEN 'shared'
                                 WHEN sl.is_public = TRUE        THEN 'public'
                            END AS visibility
              FROM StockLists sl
              LEFT JOIN StockListAccess sla
                     ON sl.stocklist_id = sla.stocklist_id
                    AND sla.user_id = %s
              LEFT JOIN Users u
                     ON sl.creator_id = u.user_id
             WHERE sl.is_public = TRUE
                OR sla.user_id = %s;
        '''
        cursor.execute(query, (user_id, user_id))
        results = cursor.fetchall()
        cursor.close()
        return results

    def view_user_owned_stock_lists(self, user_id):

        self.ensure_connection()
        cursor = self.conn.cursor()
        query = '''
            SELECT DISTINCT sl.stocklist_id, 
                            sl.creator_id, 
                            sl.is_public,
                            sl.created_at,
                            COUNT(sls.symbol) AS stock_count
            FROM StockLists sl
            LEFT JOIN StockListAccess sla ON sl.stocklist_id = sla.stocklist_id
            LEFT JOIN StockListStocks sls ON sl.stocklist_id = sls.stocklist_id
            WHERE sl.creator_id = %s 
            OR (sla.user_id = %s AND sla.access_role = 'owner')
            GROUP BY sl.stocklist_id, sl.creator_id, sl.is_public, sl.created_at
            ORDER BY sl.created_at DESC;
        '''
        cursor.execute(query, (user_id, user_id))
        stock_lists = cursor.fetchall()
        cursor.close()
        return stock_lists

    def compute_stock_list_value(self, user_id, stocklist_id):

        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Check if user has access to this stock list
        accessible_stock_lists = self.view_accessible_stock_lists(user_id)
        if not any([lst[0] == stocklist_id for lst in accessible_stock_lists]):
            cursor.close()
            return None
            
        # Calculate stock value using latest prices
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
                    lp.symbol,
                    COALESCE(
                        (SELECT close FROM DailyStockInfo WHERE symbol = lp.symbol AND timestamp = lp.max_time),
                        (SELECT close FROM StocksHistory WHERE symbol = lp.symbol AND timestamp = lp.max_time)
                    ) as close_price
                FROM latest_prices lp
            )
            SELECT SUM(sls.num_shares * cp.close_price)
            FROM StockListStocks sls
            JOIN current_prices cp ON sls.symbol = cp.symbol
            WHERE sls.stocklist_id = %s;
        '''
        cursor.execute(value_query, (stocklist_id,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            return None
        
        stock_value = d2f(result[0])
        cursor.close()
        return stock_value

    def view_stock_list_history(self, user_id, stocklist_id, period='all'):
        
        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Check if user has access to stock list
        # NOTE: we allow friends who have been shared the list to view the history
        # Makes sense if they should be reviewing it
        accessible_stock_lists = self.view_accessible_stock_lists(user_id)
        if not any([lst[0] == stocklist_id for lst in accessible_stock_lists]):
            cursor.close()
            return None
            
        # Get current stock list holdings
        holdings_query = '''
            SELECT symbol, num_shares
            FROM StockListStocks
            WHERE stocklist_id = %s
        '''
        cursor.execute(holdings_query, (stocklist_id,))
        holdings = cursor.fetchall()
        
        if not holdings:
            cursor.close()
            return None
            
        # Get the most recent date from DailyStockInfo or StocksHistory
        # for the stocks *in the stock list*, take the minimum of the max dates
        recent_date_query = '''
            SELECT MIN(max_ts)
            FROM (
                SELECT sls.symbol, MAX(combined.timestamp) as max_ts
                FROM StockListStocks sls
                JOIN (
                    SELECT symbol, timestamp FROM DailyStockInfo
                    UNION ALL
                    SELECT symbol, timestamp FROM StocksHistory
                ) combined ON sls.symbol = combined.symbol
                WHERE sls.stocklist_id = %s
                GROUP BY sls.symbol
            ) AS symbol_max_dates;
        '''
        cursor.execute(recent_date_query, (stocklist_id,))
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
            
        # Get historical data for all stocks in the list
        history_query = '''
            WITH list_dates AS (
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
                    ld.timestamp,
                    sls.symbol,
                    sls.num_shares,
                    COALESCE(sh.close, dsi.close) as close_price
                FROM list_dates ld
                CROSS JOIN (
                    SELECT symbol, num_shares
                    FROM StockListStocks
                    WHERE stocklist_id = %s
                ) sls
                LEFT JOIN StocksHistory sh ON sh.symbol = sls.symbol AND sh.timestamp = ld.timestamp
                LEFT JOIN DailyStockInfo dsi ON dsi.symbol = sls.symbol AND dsi.timestamp = ld.timestamp
            )
            SELECT 
                timestamp,
                SUM(num_shares * close_price) as total_value
            FROM stock_values
            GROUP BY timestamp
            ORDER BY timestamp ASC;
        '''
        
        cursor.execute(history_query, (start_date, latest_date, stocklist_id))
        history = cursor.fetchall()
        cursor.close()
        return history 

    def predict_stock_list_value(self, user_id: int, stocklist_id: int, days_to_predict: int = 30) -> Tuple[List[Dict], float]:

        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Check if user has access to stock list
        accessible_lists = self.view_accessible_stock_lists(user_id)
        if stocklist_id not in [lst[0] for lst in accessible_lists]:
            cursor.close()
            return [], 0.0
            
        # Get the minimum of maximum dates for all stocks in the list
        max_dates_query = '''
            SELECT MIN(max_ts)
            FROM (
                SELECT sls.symbol, MAX(combined.timestamp) as max_ts
                FROM StockListStocks sls
                JOIN (
                    SELECT symbol, timestamp FROM StocksHistory
                    UNION ALL
                    SELECT symbol, timestamp FROM DailyStockInfo
                ) combined ON sls.symbol = combined.symbol
                WHERE sls.stocklist_id = %s
                GROUP BY sls.symbol
            ) AS symbol_max_dates;
        '''
        cursor.execute(max_dates_query, (stocklist_id,))
        latest_date = cursor.fetchone()[0]
        
        if not latest_date:
            cursor.close()
            return [], 0.0
            
        # Get historical stock list values up to the latest common date
        history_query = '''
            WITH list_dates AS (
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
                    ld.timestamp,
                    sls.symbol,
                    sls.num_shares,
                    COALESCE(sh.close, dsi.close) as close_price
                FROM list_dates ld
                CROSS JOIN (
                    SELECT symbol, num_shares
                    FROM StockListStocks
                    WHERE stocklist_id = %s
                ) sls
                LEFT JOIN StocksHistory sh ON sh.symbol = sls.symbol AND sh.timestamp = ld.timestamp
                LEFT JOIN DailyStockInfo dsi ON dsi.symbol = sls.symbol AND dsi.timestamp = ld.timestamp
            )
            SELECT 
                timestamp,
                SUM(num_shares * close_price) as total_value
            FROM stock_values
            GROUP BY timestamp
            ORDER BY timestamp ASC;
        '''
        
        cursor.execute(history_query, (latest_date, stocklist_id))
        list_data = [{'timestamp': row[0].strftime('%Y-%m-%d'), 'value': float(row[1])} 
                    for row in cursor.fetchall()]
        
        cursor.close()
        
        # Use prediction model
        from models.prediction_model import StockListPredictionModel
        model = StockListPredictionModel()
        return model.predict_stock_list_value(list_data, days_to_predict) 

    def compute_stock_list_analytics(self, user_id, stocklist_id, start_date=None, end_date=None):

        self.ensure_connection()
        cursor = self.conn.cursor()
        
        # Check if user has access to stock list
        accessible_stock_lists = self.view_accessible_stock_lists(user_id)
        if not any([lst[0] == stocklist_id for lst in accessible_stock_lists]):
            cursor.close()
            return None
        
        if not end_date and not start_date:
            recent_date_query = '''
                SELECT MIN(max_ts)
                FROM (
                    SELECT sls.symbol, MAX(combined.timestamp) as max_ts
                    FROM StockListStocks sls
                    JOIN (
                        SELECT symbol, timestamp FROM DailyStockInfo
                        UNION ALL
                        SELECT symbol, timestamp FROM StocksHistory
                    ) combined ON sls.symbol = combined.symbol
                    WHERE sls.stocklist_id = %s
                    GROUP BY sls.symbol
                ) AS symbol_max_dates;
            '''
            cursor.execute(recent_date_query, (stocklist_id,))
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
            cursor.execute(earliest_date_query, (stocklist_id,))
            start_date = cursor.fetchone()[0]
            
        # Get all stocks in stock list
        stocks_query = '''
            SELECT DISTINCT symbol, num_shares
            FROM StockListStocks
            WHERE stocklist_id = %s
        '''
        cursor.execute(stocks_query, (stocklist_id,))
        stock_list_stocks = cursor.fetchall()
        
        if not stock_list_stocks:
            print("No stocks in stock list")
            cursor.close()
            return None
            
        # Check if SPY data is available for the date range
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
        symbols = tuple(stock[0] for stock in stock_list_stocks)
        params = (symbols, start_date, end_date, symbols, start_date, end_date,
                 start_date, end_date)
        
        cursor.execute(analytics_query, params)
        analytics_data = cursor.fetchall()
        
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
                    'shares': next(stock[1] for stock in stock_list_stocks if stock[0] == symbol),
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
        
        cursor.close()
        return {
            'stock_analytics': stock_analytics,
            'correlation_matrix': correlation_matrix,
            'covariance_matrix': covariance_matrix
        } 