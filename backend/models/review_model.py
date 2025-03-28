class ReviewManager:
    """
    Class for managing stock list reviews
    
    Provides functionality for writing, editing, deleting, and searching reviews
    """
    
    def __init__(self):
        self.max_review_length = 4000  # Maximum review length (requirement: 4000 characters)
    
    def validate_review(self, review_text):
        """
        Validates if the review text is valid.
        
        Args:
            review_text: Review text to validate
            
        Returns:
            Validity and error message (if any)
        """
        if not review_text or not review_text.strip():
            return False, "Review content cannot be empty."
            
        if len(review_text) > self.max_review_length:
            return False, f"Reviews can be at most {self.max_review_length} characters long."
            
        return True, None
    
    def is_accessible_by_user(self, stocklist, user_id):
        """
        Checks if a user can access a stock list.
        
        Args:
            stocklist: Stock list information
            user_id: ID of the user requesting access
            
        Returns:
            Whether access is allowed
        """
        # Public lists are accessible to everyone
        if stocklist.get('is_public', False):
            return True
            
        # Creator always has access
        if stocklist.get('creator_id') == user_id:
            return True
            
        # Check if user is in shared list
        shared_with = stocklist.get('shared_with', [])
        return user_id in shared_with
    
    def can_view_review(self, review, stocklist, user_id):
        """
        Checks if a user can view a review.
        
        Args:
            review: Review information
            stocklist: Stock list information
            user_id: ID of the user requesting access
            
        Returns:
            Whether access is allowed
        """
        # Reviews of public stock lists can be seen by anyone
        if stocklist.get('is_public', False):
            return True
            
        # Only the review author or stock list creator can view
        return (review.get('user_id') == user_id or
                stocklist.get('creator_id') == user_id) 