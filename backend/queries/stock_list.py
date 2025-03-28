import psycopg2
from queries.utils import decimal_to_float as d2f

class StockList:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='postgres',
        user='postgres',
        password='2357'
    )

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
    
    def add_stock_to_list(self, user_id, stocklist_id, symbol, num_shares):
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

    def remove_stock_from_list(self, user_id, stocklist_id, symbol, num_shares):
        """
        Decrease shares without dropping below zero.
        If resulting shares == 0, remove the record.
        """
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

    def view_stock_list(self, user_id, stocklist_id):
        """
        Return all stocks in the specified list, including the creator's ID.
        """
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
        """
        Share an existing stock list with a friend. Must verify that the person
        sharing the list is the owner
        """
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
        friends = self.view_friends(owner_id)
        friend_ids = [f[0] for f in friends]
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