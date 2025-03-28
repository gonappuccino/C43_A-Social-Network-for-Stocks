// Stock data model
export interface Stock {
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: string;
}

// Stock list model
export interface StockList {
  stocklist_id: number;
  list_name: string;
  creator_id: number;
  is_public: boolean;
  created_at: string;
  stocks?: StockListStock[];
}

// Stock in stock list
export interface StockListStock {
  symbol: string;
  num_shares: number;
}

// Stock prediction model
export interface StockPrediction {
  symbol: string;
  predicted_prices: Array<{
    date: string;
    price: number;
  }>;
  confidence: number;
} 