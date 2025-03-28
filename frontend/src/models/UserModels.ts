// User model
export interface User {
  user_id: number;
  username: string;
  email: string;
  created_at: string;
}

// Login information
export interface LoginInfo {
  email: string;
  password: string;
}

// Registration information
export interface RegisterInfo {
  username: string;
  email: string;
  password: string;
}

// Friend request model
export interface FriendRequest {
  request_id: number;
  sender_id: number;
  receiver_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
  sender_name?: string;
} 