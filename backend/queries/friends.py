import psycopg2
from queries.utils import decimal_to_float as d2f

class Friends:
    conn = psycopg2.connect(
        host='34.130.75.185',
        database='template1',
        user='postgres',
        password='2357'
    )

    def send_friend_request(self, sender_id, receiver_id):

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
                               updated_at = CURRENT_TIMESTAMP,
                               sender_id = %s,
                               receiver_id = %s
                         WHERE request_id = %s
                        RETURNING request_id;
                    '''
                    cursor.execute(update_query, (sender_id, receiver_id, request_id))
                    # send_id and receiver_id need to be updated because in the previous request
                    # they could have been swapped, and this sent request would show
                    # as an incoming request to the one who sent it.
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
        cursor = self.conn.cursor()
        query = '''
            SELECT 
                CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END AS friend_id,
                CASE WHEN sender_id = %s THEN u2.username ELSE u1.username END AS friend_name
            FROM FriendRequest 
            LEFT JOIN Users u1 ON sender_id = u1.user_id
            LEFT JOIN Users u2 ON receiver_id = u2.user_id
            WHERE (sender_id = %s OR receiver_id = %s)
            AND status = 'accepted';
        '''
        cursor.execute(query, (user_id, user_id, user_id, user_id))
        friends = cursor.fetchall()
        cursor.close()
        return friends

    def view_incoming_requests(self, user_id):
        cursor = self.conn.cursor()
        query = '''
            SELECT request_id, sender_id, u.username AS sender_name
              FROM FriendRequest LEFT JOIN Users u ON sender_id = u.user_id
             WHERE receiver_id = %s
               AND status = 'pending';
        '''
        cursor.execute(query, (user_id,))
        incoming = cursor.fetchall()
        cursor.close()
        return incoming

    def view_outgoing_requests(self, user_id):
        cursor = self.conn.cursor()
        query = '''
            SELECT request_id, receiver_id, u.username AS receiver_name
              FROM FriendRequest LEFT JOIN Users u ON receiver_id = u.user_id
             WHERE sender_id = %s
               AND status = 'pending';
        '''
        cursor.execute(query, (user_id,))
        outgoing = cursor.fetchall()
        cursor.close()
        return outgoing

    def accept_friend_request(self, request_id, user_id):
        cursor = self.conn.cursor()
        query = '''
            UPDATE FriendRequest
               SET status = 'accepted',
                   updated_at = CURRENT_TIMESTAMP
             WHERE request_id = %s
               AND status = 'pending'
               AND receiver_id = %s
            RETURNING request_id;
        '''
        cursor.execute(query, (request_id, user_id))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def reject_friend_request(self, request_id, user_id):
        cursor = self.conn.cursor()
        query = '''
            UPDATE FriendRequest
               SET status = 'rejected',
                   updated_at = CURRENT_TIMESTAMP
             WHERE request_id = %s
               AND status = 'pending'
                AND (receiver_id = %s OR sender_id = %s)
            RETURNING request_id;
        '''
        cursor.execute(query, (request_id, user_id, user_id))
        result = cursor.fetchone()
        self.conn.commit()
        cursor.close()
        return result

    def delete_friend(self, user_id, friend_id):

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