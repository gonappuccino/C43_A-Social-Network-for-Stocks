import psycopg2
from queries.utils import decimal_to_float as d2f
from queries.stock_list import StockList

class Reviews:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='template1',
        user='postgres',
        password='2357'
    )
    stock_list = StockList()

    def create_review(self, user_id, stocklist_id, review_text):

        if len(review_text) > 4000:
            return None
        cursor = self.conn.cursor()
        
        # 1) Check if the user has access to the stock list
        accessible_lists = self.stock_list.view_accessible_stock_lists(user_id)
        if not any([lst[0] == stocklist_id for lst in accessible_lists]):
            cursor.close()
            return None

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

        cursor = self.conn.cursor()

        # check access
        access_query = '''
            SELECT sl.is_public, sl.creator_id, sla.access_role
            FROM StockLists sl
            LEFT JOIN StockListAccess sla ON sl.stocklist_id = sla.stocklist_id AND sla.user_id = %s
            WHERE sl.stocklist_id = %s
        '''
        cursor.execute(access_query, (user_id, stocklist_id))
        access_info = cursor.fetchone()
        
        if not access_info:
            cursor.close()
            return []  # stock list doesn't exist
            
        is_public, list_owner, access_role = access_info
        
        # check access
        has_access = is_public or list_owner == user_id or access_role in ('owner', 'shared')
        
        if not has_access:
            cursor.close()
            return []  # user doesn't have access to this stock list
        
        # can only see all reviews if the stock list is public or the user is the owner
        # Otherwise, if the stocklist was shared with the user, only see reviews made by that user (who should be a friend of the owner)
        if is_public or list_owner == user_id:
            # get reviews
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
            results = cursor.fetchall()
            cursor.close()
            return results
        elif access_role == 'shared':
            # Only get reviews made by the friend on the stock list
            query = '''
                SELECT r.review_id,
                r.user_id,
                r.review_text,
                r.created_at,
                r.updated_at
                FROM Reviews r
                WHERE r.user_id = %s AND r.stocklist_id = %s
                ORDER BY r.created_at ASC;
            '''
            cursor.execute(query, (user_id, stocklist_id))
            results = cursor.fetchall()
            cursor.close()
            return results
        else:
            cursor.close()
            return []
