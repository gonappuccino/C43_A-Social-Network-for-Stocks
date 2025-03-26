import psycopg2
from queries.utils import decimal_to_float as d2f

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
            SELECT close
              FROM StocksHistory
             WHERE symbol = %s
             ORDER BY timestamp DESC
             LIMIT 1;
        '''
        cursor.execute(price_query, (symbol,))
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

        # Get the latest price per share from StockHistory
        price_query = '''
            SELECT close
              FROM StocksHistory
             WHERE symbol = %s
             ORDER BY timestamp DESC
             LIMIT 1;
        '''
        cursor.execute(price_query, (symbol,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            return None
        price_per_share = d2f(result[0])
        
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
            SELECT close
              FROM StocksHistory
             WHERE symbol = %s
             ORDER BY timestamp DESC
             LIMIT 1;
        '''
        cursor.execute(price_query, (symbol,))
        price_per_share = cursor.fetchone()[0]
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
                  FROM StocksHistory
                 GROUP BY symbol
              ) AS latest ON ps.symbol = latest.symbol
              JOIN StocksHistory sh 
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