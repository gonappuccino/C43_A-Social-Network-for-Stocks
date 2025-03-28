// Review model
export interface Review {
  review_id: number;
  user_id: number;
  stocklist_id: number;
  review_text: string;
  created_at: string;
  updated_at: string;
  reviewer_name?: string; // Reviewer name
} 