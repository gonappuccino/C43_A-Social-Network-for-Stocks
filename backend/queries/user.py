import psycopg2
from flask import Flask, request
import yfinance as yf
import datetime

from queries.utils import decimal_to_float as d2f
class User:
    conn = psycopg2.connect(
        host='34.130.75.185',
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
        return True

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
        
        # First check if the user owns this portfolio
        check_query = '''
            SELECT portfolio_id 
            FROM Portfolios 
            WHERE portfolio_id = %s AND user_id = %s
        '''
        cursor.execute(check_query, (portfolio_id, user_id))
        is_owner = cursor.fetchone()
        
        if not is_owner:
            cursor.close()
            return None  # User is not the owner
        
        # Proceed with deletion
        delete_query = '''
            DELETE FROM Portfolios
            WHERE portfolio_id = %s
            RETURNING portfolio_id;
        '''
        cursor.execute(delete_query, (portfolio_id,))
        deleted_id = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return deleted_id

    def update_cash_balance(self, portfolio_id, amount, record_transaction=True):

        # If amount is negative, check if the portfolio has enough cash to withdraw
        if amount < 0:
            cursor = self.conn.cursor()
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
            
        cursor = self.conn.cursor()
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

    def buy_stock_shares(self, portfolio_id, symbol, num_shares):
        cursor = self.conn.cursor()

        # Get the latest price per share from StockHistory
        price_query = '''
            SELECT close
              FROM StocksHistory
             WHERE symbol = %s
             ORDER BY timestamp DESC
             LIMIT 1;
        '''
        cursor.execute(price_query, (symbol,))
        price_per_share = d2f(cursor.fetchone()[0])
        if not price_per_share:
            cursor.close()
            return None  # No price data available
        
        # Calculate the total cost and check if the portfolio has enough cash
        total_cost = num_shares * price_per_share

        result = self.update_cash_balance(portfolio_id, -total_cost, record_transaction=False)
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
    
    def sell_stock_shares(self, portfolio_id, symbol, num_shares, price_per_share):
        """
        Decrease shares without dropping below zero.
        If resulting shares == 0, remove the record.
        """
        cursor = self.conn.cursor()

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
        self.update_cash_balance(portfolio_id, total_revenue, record_transaction=False)

        # Record the transaction
        transaction_query = '''
            INSERT INTO PortfolioTransactions (portfolio_id, symbol, transaction_type, shares, price, cash_change)
            VALUES (%s, %s, 'SELL', %s, %s, %s)
        '''
        cursor.execute(transaction_query, (portfolio_id, symbol, num_shares, price_per_share, total_revenue))

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

    def view_portfolio_transactions(self, portfolio_id):
        """
        View all transactions for a given portfolio.
        """
        cursor = self.conn.cursor()
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

    def compute_portfolio_value(self, portfolio_id):
        """
        Returns the total current market value of the given portfolio, 
        including its cash balance and the latest stock prices.
        """
        cursor = self.conn.cursor()

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
        stock_value = d2f(cursor.fetchone()[0])
        if not stock_value:
            cursor.close()
            return cash_balance

        total_value = float(cash_balance) + float(stock_value)

        cursor.close()
        return total_value

    def create_stock_list(self, creator_id, list_name, is_public=False):
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
        """
        Delete a stock list by its ID, but only if the specified user is the owner.
        """
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
        """
        Decrease shares without dropping below zero.
        If resulting shares == 0, remove the record.
        """
        cursor = self.conn.cursor()

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
                RETURNING list_entry_id;
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
                RETURNING list_entry_id, num_shares;
            '''
            cursor.execute(update_query, (num_shares, stocklist_id, symbol))
            result = cursor.fetchone()
            self.conn.commit()
            cursor.close()
            return result

    def view_stock_list(self, stocklist_id):
        """
        Return all stocks in the specified list, including the creator's ID.
        
        """
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

    def send_friend_request(self, sender_id, receiver_id):
        """
        Insert a new friend request if it does not exist, or if the previous
        one was rejected more than 5 minutes ago. Otherwise do nothing.
        """

        if sender_id == receiver_id:
            return -3
        cursor = self.conn.cursor()
        # Check if there's an existing request
        check_query = '''
            SELECT request_id, status, updated_at
              FROM FriendRequest
             WHERE (sender_id = %s AND receiver_id = %s)
             OR   (sender_id = %s AND receiver_id = %s);
        '''
        cursor.execute(check_query, (sender_id, receiver_id, receiver_id, sender_id))
        existing = cursor.fetchone()

        if existing:
            request_id, status, updated_at = existing
            # If pending or accepted, do nothing (already friends or pending)
            if status in ('pending', 'accepted'):
                cursor.close()
                return -1 # Error code for already pending/accepted
            # If rejected, allow re-send after 5 minutes
            else: 
                time_check_query = '''
                    SELECT EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - %s)) / 60
                '''
                cursor.execute(time_check_query, (updated_at,))
                minutes_passed = cursor.fetchone()[0]
                if minutes_passed >= 5:
                    update_query = '''
                        UPDATE FriendRequest
                           SET status = 'pending',
                               updated_at = CURRENT_TIMESTAMP
                         WHERE request_id = %s
                        RETURNING request_id;
                    '''
                    cursor.execute(update_query, (request_id,))
                    updated_id = cursor.fetchone()[0]
                    self.conn.commit()
                    cursor.close()
                    return updated_id
                else:
                    cursor.close()
                    return -2 # Error code for too soon to re-send
        else:
            # Insert a new friend request
            insert_query = '''
                INSERT INTO FriendRequest (sender_id, receiver_id, status)
                VALUES (%s, %s, 'pending')
                RETURNING request_id;
            '''
            cursor.execute(insert_query, (sender_id, receiver_id))
            new_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            return new_id

    def view_friends(self, user_id):
        """
        Return a list of user_ids who are friends with the given user (status = accepted).
        """
        cursor = self.conn.cursor()
        query = '''
            SELECT CASE WHEN sender_id = %s THEN receiver_id 
                        ELSE sender_id END AS friend_id
              FROM FriendRequest
             WHERE (sender_id = %s OR receiver_id = %s)
               AND status = 'accepted';
        '''
        cursor.execute(query, (user_id, user_id, user_id))
        friends = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return friends

    def view_incoming_requests(self, user_id):
        """
        Return all pending friend requests where this user is the receiver.
        """
        cursor = self.conn.cursor()
        query = '''
            SELECT request_id, sender_id
              FROM FriendRequest
             WHERE receiver_id = %s
               AND status = 'pending';
        '''
        cursor.execute(query, (user_id,))
        incoming = cursor.fetchall()
        cursor.close()
        return incoming

    def view_outgoing_requests(self, user_id):
        """
        Return all pending friend requests where this user is the sender.
        """
        cursor = self.conn.cursor()
        query = '''
            SELECT request_id, receiver_id
              FROM FriendRequest
             WHERE sender_id = %s
               AND status = 'pending';
        '''
        cursor.execute(query, (user_id,))
        outgoing = cursor.fetchall()
        cursor.close()
        return outgoing

    def accept_friend_request(self, request_id):
        """
        Accept a friend request by setting status to 'accepted'.
        """
        cursor = self.conn.cursor()
        query = '''
            UPDATE FriendRequest
               SET status = 'accepted',
                   updated_at = CURRENT_TIMESTAMP
             WHERE request_id = %s
               AND status = 'pending'
            RETURNING request_id;
        '''
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def reject_friend_request(self, request_id):
        """
        Reject a friend request by setting status to 'rejected'.
        """
        cursor = self.conn.cursor()
        query = '''
            UPDATE FriendRequest
               SET status = 'rejected',
                   updated_at = CURRENT_TIMESTAMP
             WHERE request_id = %s
               AND status = 'pending'
            RETURNING request_id;
        '''
        cursor.execute(query, (request_id,))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def delete_friend(self, user_id, friend_id):
        """
        If two users are friends, update the row to 'rejected' so a new request
        can be sent later, following the same 5-minute rule.
        
        Also removes access to all non-public stock lists that were shared between them.
        """
        cursor = self.conn.cursor()
        # First update the friendship status
        query = '''
            UPDATE FriendRequest
            SET status = 'rejected',
                updated_at = CURRENT_TIMESTAMP
            WHERE ((sender_id = %s AND receiver_id = %s)
                OR  (sender_id = %s AND receiver_id = %s))
            AND status = 'accepted'
            RETURNING request_id;
        '''
        cursor.execute(query, (user_id, friend_id, friend_id, user_id))
        result = cursor.fetchone()
        
        if result:
            # Remove stock lists shared by user_id to friend_id
            remove_shared_access_query = '''
                DELETE FROM StockListAccess
                WHERE stocklist_id IN (
                    SELECT sla1.stocklist_id
                    FROM StockListAccess sla1
                    JOIN StockListAccess sla2 ON sla1.stocklist_id = sla2.stocklist_id
                    JOIN StockLists sl ON sla1.stocklist_id = sl.stocklist_id
                    WHERE sla1.user_id = %s AND sla1.access_role = 'owner'
                    AND sla2.user_id = %s AND sla2.access_role = 'shared'
                    AND sl.is_public = FALSE
                )
                AND user_id = %s
                AND access_role = 'shared'
            '''
            cursor.execute(remove_shared_access_query, (user_id, friend_id, friend_id))
            
            # Also remove stock lists shared by friend_id to user_id (in case friend is also an owner)
            cursor.execute(remove_shared_access_query, (friend_id, user_id, user_id))
        
        self.conn.commit()
        cursor.close()
        return result
    
    def share_stock_list(self, stocklist_id, owner_id, friend_id):
        """
        Share an existing stock list with a friend. Must verify that
        'owner_id' is indeed the list’s creator or has 'owner' role.
        """
        cursor = self.conn.cursor()
        # Check if the caller actually owns this list or is in owner role
        check_owner_query = '''
            SELECT 1
              FROM StockListAccess
             WHERE stocklist_id = %s AND user_id = %s AND access_role = 'owner';
        '''
        cursor.execute(check_owner_query, (stocklist_id, owner_id))
        is_owner = cursor.fetchone()
        if not is_owner:
            cursor.close()
            return None  # Caller is not the owner.
        
        # Check if friend_id is actually a friend of owner_id
        friends = self.view_friends(owner_id)
        if friend_id not in friends:
            cursor.close()
            return None  # Friend is not a friend of the owner.

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
        return True

    def unshare_stock_list(self, stocklist_id, owner_id, friend_id):
        """
        Remove access to a stock list for a specific friend.
        Must verify that 'owner_id' is indeed the list's creator or has 'owner' role.
        
        Returns:
        - True: If unsharing was successful
        - None: If owner_id is not the owner or friend_id had no access
        """
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
        """
        Return all stock lists that the user can see:
          - Lists in StockListAccess where user_id matches
          - Any StockLists marked is_public = TRUE
        """
        cursor = self.conn.cursor()
        query = '''
            SELECT DISTINCT sl.stocklist_id,
                            sl.list_name,
                            sl.creator_id,
                            sl.is_public,
                            CASE WHEN sla.access_role = 'owner' THEN 'private'
                                 WHEN sla.access_role = 'shared' THEN 'shared'
                                 WHEN sl.is_public = TRUE        THEN 'public'
                            END AS visibility
              FROM StockLists sl
              LEFT JOIN StockListAccess sla
                     ON sl.stocklist_id = sla.stocklist_id
                    AND sla.user_id = %s
             WHERE sl.is_public = TRUE
                OR sla.user_id = %s;
        '''
        cursor.execute(query, (user_id, user_id))
        results = cursor.fetchall()
        cursor.close()
        return results

    def create_review(self, user_id, stocklist_id, review_text):
        """
        Write a new review for a stock list, if the user does not have one already
        and has access to the stock list (public or shared/owner). 
        """
        cursor = self.conn.cursor()

        # 1) Check if user can access the stock list:
        #    - If stocklist is public, or
        #    - If user is in StockListAccess with 'owner' or 'shared', or
        #    - user_id is the stock list creator (the 'user_id' column in StockLists).
        access_query = '''
            SELECT sl.stocklist_id
              FROM StockLists sl
              LEFT JOIN StockListAccess sla 
                     ON sl.stocklist_id = sla.stocklist_id 
                    AND sla.user_id = %s
             WHERE sl.stocklist_id = %s
               AND (sl.is_public = TRUE
                    OR sl.creator_id = %s
                    OR sla.access_role IN ('owner','shared'));
        '''
        cursor.execute(access_query, (user_id, stocklist_id, user_id))
        can_access = cursor.fetchone()
        if not can_access:
            cursor.close()
            return None  # user has no access

        # 2) Check if the user already has a review for this stock list
        check_query = '''
            SELECT review_id 
              FROM Reviews
             WHERE user_id = %s AND stocklist_id = %s;
        '''
        cursor.execute(check_query, (user_id, stocklist_id))
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            return None  # user already reviewed this list

        # 3) Insert the new review
        insert_query = '''
            INSERT INTO Reviews (user_id, stocklist_id, review_text)
            VALUES (%s, %s, %s)
            RETURNING review_id;
        '''
        cursor.execute(insert_query, (user_id, stocklist_id, review_text))
        new_review_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return new_review_id

    def update_review(self, review_id, user_id, new_text):
        """
        Edit a review if the user is the author. 
        """
        cursor = self.conn.cursor()
        # 1) Check if user is indeed the author
        check_query = '''
            SELECT review_id 
              FROM Reviews
             WHERE review_id = %s AND user_id = %s;
        '''
        cursor.execute(check_query, (review_id, user_id))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            return None  # not the author, or no such review

        # 2) Update the text
        update_query = '''
            UPDATE Reviews
               SET review_text = %s,
                   updated_at = CURRENT_TIMESTAMP
             WHERE review_id = %s
            RETURNING review_id;
        '''
        cursor.execute(update_query, (new_text, review_id))
        updated = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return updated

    def delete_review(self, review_id, user_id):
        """
        Delete the review if the user is the author or the creator of the stock list.
        """
        cursor = self.conn.cursor()
        # 1) Get the user_id of the review's author + the stocklist's creator
        check_query = '''
            SELECT r.user_id, sl.creator_id AS owner
              FROM Reviews r
              JOIN StockLists sl ON r.stocklist_id = sl.stocklist_id
             WHERE r.review_id = %s
        '''
        cursor.execute(check_query, (review_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return None  # no such review
        review_author, list_owner = row

        # 2) Decide if current user is allowed to delete
        if user_id not in (review_author, list_owner):
            cursor.close()
            return None

        # 3) Perform the delete
        delete_query = '''
            DELETE FROM Reviews
             WHERE review_id = %s
            RETURNING review_id;
        '''
        cursor.execute(delete_query, (review_id,))
        deleted_id = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return deleted_id

    def view_reviews(self, stocklist_id, user_id):
        """
        View all reviews for the specified stock list under the rules:
          - If the list is public, return all reviews.
          - If not public, only show reviews authored by `user_id` OR the user is the list owner.
        """
        cursor = self.conn.cursor()

        # 1) Check if the list is public and get the list owner
        check_query = '''
            SELECT is_public, creator_id
              FROM StockLists
             WHERE stocklist_id = %s
        '''
        cursor.execute(check_query, (stocklist_id,))
        list_info = cursor.fetchone()
        if not list_info:
            cursor.close()
            return []  # no stock list found
        is_public, list_owner = list_info

        # 2) If the list is public, the user can see all reviews
        #    Otherwise, user can see only their own reviews OR if user is the owner
        if is_public:
            query = '''
                SELECT r.review_id,
                       r.user_id,
                       r.review_text,
                       r.created_at,
                       r.updated_at
                  FROM Reviews r
                 WHERE r.stocklist_id = %s
                 ORDER BY r.created_at ASC;
            '''
            cursor.execute(query, (stocklist_id,))
        else:
            # not public => user sees only reviews by themself or from the user_id who created the list
            query = '''
                SELECT r.review_id,
                       r.user_id,
                       r.review_text,
                       r.created_at,
                       r.updated_at
                  FROM Reviews r
                 WHERE r.stocklist_id = %s
                   AND (r.user_id = %s OR %s = %s)
                 ORDER BY r.created_at ASC;
            '''
            # The condition "(r.user_id = %s OR %s = %s)" means "r.user_id = user_id OR user_id == list_owner"
            # We pass user_id, user_id, and list_owner as parameters
            cursor.execute(query, (stocklist_id, user_id, user_id, list_owner))

        results = cursor.fetchall()
        cursor.close()
        return results

    def fetch_and_store_daily_info_yahoo(self, symbol):
        """
        Fetch today's stock info for 'symbol' from Yahoo Finance 
        and insert/update it in the DailyStockInfo table.
        """
        cursor = self.conn.cursor()
        verify_symbol_query = '''
            SELECT symbol
            FROM Stocks
            WHERE symbol = %s;
        '''
        cursor.execute(verify_symbol_query, (symbol,))
        if not cursor.fetchone():
            cursor.close()
            return None
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1d")
        if data.empty:
            return None  # No data available

        last_row = data.iloc[-1]
        open_price = float(last_row["Open"])
        high_price = float(last_row["High"])
        low_price = float(last_row["Low"])
        close_price = float(last_row["Close"])
        volume = int(last_row["Volume"])
        today = datetime.date.today()

        query = '''
            INSERT INTO DailyStockInfo (symbol, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, date) 
            DO UPDATE SET open = EXCLUDED.open,
                          high = EXCLUDED.high,
                          low = EXCLUDED.low,
                          close = EXCLUDED.close,
                          volume = EXCLUDED.volume
            RETURNING daily_info_id;
        '''
        cursor.execute(query, (symbol, today, open_price, high_price, low_price, close_price, volume))
        daily_info_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()

        return daily_info_id

    def view_stock_info(self, symbol):
        """
        Return merged historical data from StocksHistory plus any daily data
        from DailyStockInfo for the specified symbol, ordered by date descending.
        """
        cursor = self.conn.cursor()
        query = '''
            SELECT timestamp::date AS record_date, open, high, low, close, volume
              FROM StocksHistory
             WHERE symbol = %s
            UNION ALL
            SELECT date AS record_date, open, high, low, close, volume
              FROM DailyStockInfo
             WHERE symbol = %s
             ORDER BY record_date DESC;
        '''
        cursor.execute(query, (symbol, symbol))
        data = cursor.fetchall()
        cursor.close()
        return data

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

    def view_user_owned_stock_lists(self, user_id):
        """
        Return all stock lists owned by the specified user (not just accessible).
        This includes lists where the user is the creator or has 'owner' access role.
        """
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
    
    

