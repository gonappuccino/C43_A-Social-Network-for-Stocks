import psycopg2
from queries.setup import setup_queries
from flask import Flask, request

class User:
    conn = psycopg2.connect(
        host='localhost',
        database='postgres',
        user='postgres',
        password='2357'
    )

    def register(self, username, password, email):
        # Check if username and email are unique
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username=%s OR email=%s", (username, email))
        if cursor.fetchone():
            cursor.close()
            return False
        
        cursor.execute("INSERT INTO Users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
        self.conn.commit()
        cursor.close()
        return True

    def login(self, email, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM Users WHERE email=%s AND password=%s", (email, password))
        user_id = cursor.fetchone()
        cursor.close()
        return user_id
    
    def logout(self):
        pass

    def create_portfolio(self, user_id, initial_cash=0):
        cursor = self.conn.cursor()
        query = '''
            INSERT INTO Portfolios (user_id, cash_balance)
            VALUES (%s, %s)
            RETURNING portfolio_id;
        '''
        cursor.execute(query, (user_id, initial_cash))
        portfolio_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return portfolio_id

    def update_cash_balance(self, portfolio_id, amount):
        cursor = self.conn.cursor()
        query = '''
            UPDATE Portfolios
            SET cash_balance = cash_balance + %s
            WHERE portfolio_id = %s
            RETURNING cash_balance;
        '''
        cursor.execute(query, (amount, portfolio_id))
        updated_balance = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return updated_balance

    def add_stock_shares(self, portfolio_id, symbol, num_shares):
        cursor = self.conn.cursor()
        query = '''
            INSERT INTO PortfolioStocks (portfolio_id, symbol, num_shares)
            VALUES (%s, %s, %s)
            ON CONFLICT (portfolio_id, symbol)
            DO UPDATE SET num_shares = PortfolioStocks.num_shares + EXCLUDED.num_shares
            RETURNING portfolio_entry_id, num_shares;
        '''
        cursor.execute(query, (portfolio_id, symbol, num_shares))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def remove_stock_shares(self, portfolio_id, symbol, num_shares):
        cursor = self.conn.cursor()
        query = '''
            UPDATE PortfolioStocks
            SET num_shares = num_shares - %s
            WHERE portfolio_id = %s AND symbol = %s
            RETURNING portfolio_entry_id, num_shares;
        '''
        cursor.execute(query, (num_shares, portfolio_id, symbol))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def view_portfolio(self, portfolio_id):
        cursor = self.conn.cursor()
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

    def create_stock_list(self, user_id, is_public=False):
        cursor = self.conn.cursor()
        query = '''
            INSERT INTO StockLists (user_id, is_public)
            VALUES (%s, %s)
            RETURNING stocklist_id;
        '''
        cursor.execute(query, (user_id, is_public))
        stocklist_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return stocklist_id

    def add_stock_to_list(self, stocklist_id, symbol, num_shares):
        cursor = self.conn.cursor()
        query = '''
            INSERT INTO StockListStocks (stocklist_id, symbol, num_shares)
            VALUES (%s, %s, %s)
            ON CONFLICT (stocklist_id, symbol)
            DO UPDATE SET num_shares = StockListStocks.num_shares + EXCLUDED.num_shares
            RETURNING list_entry_id, num_shares;
        '''
        cursor.execute(query, (stocklist_id, symbol, num_shares))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def remove_stock_from_list(self, stocklist_id, symbol, num_shares):
        cursor = self.conn.cursor()
        query = '''
            UPDATE StockListStocks
            SET num_shares = num_shares - %s
            WHERE stocklist_id = %s AND symbol = %s
            RETURNING list_entry_id, num_shares;
        '''
        cursor.execute(query, (num_shares, stocklist_id, symbol))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def view_stock_list(self, stocklist_id):
        cursor = self.conn.cursor()
        query = '''
            SELECT sl.stocklist_id, sl.is_public, sl.user_id,
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





