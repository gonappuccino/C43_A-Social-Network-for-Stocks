// Portfolio model
export interface Portfolio {
  portfolio_id: number;
  portfolio_name: string;
  user_id: number;
  cash_balance: number;
  created_at: string;
  stocks?: PortfolioStock[];
}

// Portfolio view model for UI display
export interface PortfolioView {
  id: number;
  name: string;
  userId: number;
  value: number;
  createdAt: string;
  stocks?: PortfolioStock[];
}

// Portfolio stock item
export interface PortfolioStock {
  symbol: string;
  num_shares: number;
  current_price?: number;
  total_value?: number;
}

// API Portfolio data structure
export interface ApiPortfolio {
  portfolio_id: number;
  portfolio_name: string;
  user_id: number;
  cash_balance: number;
  created_at: string;
  stocks?: ApiPortfolioStock[];
}

// API Portfolio stock item
export interface ApiPortfolioStock {
  symbol: string;
  num_shares: number;
}

// Portfolio transaction
export interface PortfolioTransaction {
  transaction_id: number;
  portfolio_id: number;
  symbol: string;
  transaction_type: 'BUY' | 'SELL' | 'CASH';
  shares: number;
  price: number;
  cash_change: number;
  transaction_time: string;
}

// Portfolio statistics
export interface PortfolioStats {
  stocks: Array<{
    symbol: string;
    cov: number;  // Coefficient of variation
    beta: number; // Beta coefficient
  }>;
  correlation_matrix: Array<Array<number>>; // Correlation matrix
}

// Helper function to calculate portfolio value
export const calculatePortfolioValue = (portfolio: ApiPortfolio): number => {
  if (!portfolio.stocks || portfolio.stocks.length === 0) {
    return portfolio.cash_balance;
  }

  // In a real app, we would use current prices from API
  // For now, we'll use a placeholder calculation (assuming $100 per share)
  const stocksValue = portfolio.stocks.reduce((total, stock) => {
    return total + (stock.num_shares * 100);
  }, 0);

  return stocksValue + portfolio.cash_balance;
};

// Convert API portfolio to UI portfolio view
export const toPortfolioView = (apiPortfolio: ApiPortfolio): PortfolioView => {
  return {
    id: apiPortfolio.portfolio_id,
    name: apiPortfolio.portfolio_name,
    userId: apiPortfolio.user_id,
    value: calculatePortfolioValue(apiPortfolio),
    createdAt: apiPortfolio.created_at,
    stocks: apiPortfolio.stocks
  };
}; 