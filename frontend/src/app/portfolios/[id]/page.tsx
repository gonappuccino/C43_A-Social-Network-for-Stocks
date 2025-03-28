'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import React from 'react';
import Navbar from '../../../components/Navbar';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

// Mock data for demonstration
const mockPortfolios = [
  { 
    id: 1, 
    name: 'Main Portfolio', 
    value: 25431.78, 
    change: 2.4, 
    dailyChange: 598.32,
    stocks: [
      { symbol: 'AAPL', shares: 10, price: 189.84, value: 1898.40, change: 1.2 },
      { symbol: 'MSFT', shares: 5, price: 421.55, value: 2107.75, change: 0.8 },
      { symbol: 'GOOGL', shares: 3, price: 174.63, value: 523.89, change: -0.5 },
      { symbol: 'AMZN', shares: 8, price: 182.41, value: 1459.28, change: 3.1 },
    ],
    cash: 1520.43 
  },
  { 
    id: 2, 
    name: 'Retirement', 
    value: 45128.91, 
    change: -0.7, 
    dailyChange: -318.32,
    stocks: [
      { symbol: 'VTI', shares: 50, price: 250.32, value: 12516.00, change: -0.2 },
      { symbol: 'VXUS', shares: 60, price: 149.75, value: 8985.00, change: -1.3 },
      { symbol: 'BND', shares: 40, price: 100.89, value: 4035.60, change: -0.3 },
    ],
    cash: 2100.00 
  },
  { 
    id: 3, 
    name: 'Tech Stocks', 
    value: 12890.55, 
    change: 5.2, 
    dailyChange: 638.22,
    stocks: [
      { symbol: 'NVDA', shares: 2, price: 913.20, value: 1826.40, change: 8.5 },
      { symbol: 'TSLA', shares: 8, price: 267.48, value: 2139.84, change: 6.2 },
      { symbol: 'AMD', shares: 15, price: 178.90, value: 2683.50, change: 4.1 },
    ],
    cash: 500.20 
  },
];

// Mock historical data for stocks
const generateHistoricalData = (symbol: string, days: number) => {
  const data = [];
  const today = new Date();
  let basePrice = 100;
  
  // Choose a different base price based on symbol to make charts look different
  if (symbol === 'AAPL') basePrice = 180;
  if (symbol === 'MSFT') basePrice = 400;
  if (symbol === 'GOOGL') basePrice = 170;
  if (symbol === 'AMZN') basePrice = 180;
  if (symbol === 'NVDA') basePrice = 900;
  if (symbol === 'TSLA') basePrice = 260;
  if (symbol === 'AMD') basePrice = 180;
  if (symbol === 'VTI') basePrice = 250;
  if (symbol === 'VXUS') basePrice = 150;
  if (symbol === 'BND') basePrice = 100;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(today.getDate() - i);
    
    // Add some randomness to simulate real stock movement
    const randomFactor = 0.02; // 2% random movement
    const dailyChange = basePrice * randomFactor * (Math.random() * 2 - 1);
    basePrice += dailyChange;
    
    data.push({
      date: date.toISOString().split('T')[0],
      price: parseFloat(basePrice.toFixed(2))
    });
  }
  
  return data;
};

// Mock prediction function
const predictStockPrice = (symbol: string, days: number) => {
  // Get historical data for the last 30 days
  const historical = generateHistoricalData(symbol, 30);
  
  // Last known price
  const lastPrice = historical[historical.length - 1].price;
  const predictedData = [];
  
  // Generate prediction data
  const today = new Date();
  
  for (let i = 1; i <= days; i++) {
    const date = new Date();
    date.setDate(today.getDate() + i);
    
    // Simple prediction logic (random walk with trend)
    // In a real app, this would be replaced with actual prediction from backend
    const randomChange = lastPrice * 0.01 * (Math.random() * 2 - 0.8); // Slight upward bias
    const predictedPrice = lastPrice + (randomChange * i);
    
    predictedData.push({
      date: date.toISOString().split('T')[0],
      price: parseFloat(predictedPrice.toFixed(2))
    });
  }
  
  // Return object with the structure matching the StockPrediction interface
  return {
    symbol,
    predicted_prices: predictedData,
    confidence: parseFloat((0.5 + Math.random() * 0.4).toFixed(2)) // Random confidence between 0.5-0.9
  };
};

// Define the type for params
interface PageParams {
  id: string;
}

export default function PortfolioDetail({ params }: { params: any }) {
  const router = useRouter();
  // Properly unwrap params using React.use() with correct typing
  const unwrappedParams = React.use(params) as PageParams;
  const [portfolio, setPortfolio] = useState<any>(null);
  const [selectedStock, setSelectedStock] = useState<string | null>(null);
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [predictionData, setPredictionData] = useState<any>(null);
  const [predictionDays, setPredictionDays] = useState<number>(30);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  const [portfolioId, setPortfolioId] = useState<number>(0);
  
  // Initialize the portfolio ID from params (only runs once)
  useEffect(() => {
    try {
      const id = unwrappedParams && unwrappedParams.id ? parseInt(unwrappedParams.id, 10) : 0;
      setPortfolioId(id);
    } catch (error) {
      console.error('Error parsing portfolio ID:', error);
      setPortfolioId(0);
    }
  }, [unwrappedParams]); // Dependency on unwrappedParams

  // Load portfolio data when portfolioId changes
  useEffect(() => {
    if (portfolioId === 0) return;
    
    try {
      // In a real app, fetch portfolio data from API
      const portfolioData = mockPortfolios.find(p => p.id === portfolioId);
      
      if (portfolioData) {
        setPortfolio(portfolioData);
        
        // If portfolio has stocks, select the first one by default
        if (portfolioData.stocks && portfolioData.stocks.length > 0) {
          setSelectedStock(portfolioData.stocks[0].symbol);
          
          // Load historical data for first stock
          const historicalData = generateHistoricalData(portfolioData.stocks[0].symbol, 30);
          setHistoricalData(historicalData);
          
          // Load prediction data for first stock
          const prediction = predictStockPrice(portfolioData.stocks[0].symbol, predictionDays);
          setPredictionData(prediction);
        }
      }
    } catch (error) {
      console.error('Error loading portfolio data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [portfolioId, predictionDays]);

  const handleStockSelect = (symbol: string) => {
    setSelectedStock(symbol);
    
    // Load historical data
    const historicalData = generateHistoricalData(symbol, 30);
    setHistoricalData(historicalData);
    
    // Load prediction data
    const prediction = predictStockPrice(symbol, predictionDays);
    setPredictionData(prediction);
  };

  const handleChangePredictionDays = (days: number) => {
    setPredictionDays(days);
    
    if (selectedStock) {
      // Update prediction with new time frame
      const prediction = predictStockPrice(selectedStock, days);
      setPredictionData(prediction);
    }
  };

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <p className="text-xl text-gray-600 dark:text-gray-400">Loading portfolio data...</p>
          </div>
        </div>
      </>
    );
  }

  if (!portfolio) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">Portfolio Not Found</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">The portfolio you're looking for doesn't exist.</p>
            <button
              onClick={() => router.push('/portfolios')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Return to Portfolios
            </button>
          </div>
        </div>
      </>
    );
  }

  // Combine historical and prediction data for chart
  const chartData = [
    ...historicalData,
    ...(predictionData ? predictionData.predicted_prices : [])
  ];

  // Find the index where predictions start
  const predictionStartIndex = historicalData.length;

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <main className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{portfolio.name}</h1>
              <div className="text-right">
                <p className="text-xl text-gray-900 dark:text-white">
                  Total Value: <span className="font-bold">${portfolio.value.toLocaleString()}</span>
                </p>
                <p className={`text-sm ${portfolio.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {portfolio.change >= 0 ? '+' : ''}{portfolio.change.toFixed(2)}% (${portfolio.dailyChange >= 0 ? '+' : ''}{portfolio.dailyChange.toLocaleString()})
                </p>
              </div>
            </div>
            
            <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Stock List */}
              <div className="lg:col-span-1">
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
                  <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                      Portfolio Holdings
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Cash: ${portfolio.cash.toLocaleString()}
                    </p>
                  </div>
                  <div className="border-t border-gray-200 dark:border-gray-700">
                    <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                      {portfolio.stocks.map((stock: any) => (
                        <li 
                          key={stock.symbol}
                          className={`px-4 py-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${selectedStock === stock.symbol ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''}`}
                          onClick={() => handleStockSelect(stock.symbol)}
                        >
                          <div className="flex justify-between">
                            <div>
                              <p className="text-sm font-medium text-gray-900 dark:text-white">
                                {stock.symbol}
                              </p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                {stock.shares} shares
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-gray-900 dark:text-white">
                                ${stock.value.toLocaleString()}
                              </p>
                              <p className={`text-xs ${stock.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                                {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}%
                              </p>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
              
              {/* Stock Chart and Prediction */}
              <div className="lg:col-span-2">
                {selectedStock ? (
                  <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
                    <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        {selectedStock} - Historical & Predicted Price
                      </h3>
                      
                      {/* Prediction options */}
                      <div className="flex space-x-2">
                        <select
                          value={predictionDays}
                          onChange={(e) => handleChangePredictionDays(parseInt(e.target.value))}
                          className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white"
                        >
                          <option value={7}>7 Days</option>
                          <option value={14}>14 Days</option>
                          <option value={30}>30 Days</option>
                          <option value={60}>60 Days</option>
                          <option value={90}>90 Days</option>
                        </select>
                      </div>
                    </div>
                    
                    <div className="px-4 py-5 sm:p-6">
                      {/* Prediction confidence */}
                      {predictionData && (
                        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm text-gray-500 dark:text-gray-400">Prediction Confidence</p>
                              <p className="text-lg font-medium text-gray-900 dark:text-white">
                                {(predictionData.confidence * 100).toFixed(0)}%
                              </p>
                            </div>
                            <div>
                              <div className="h-2 w-24 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-indigo-600 dark:bg-indigo-500 rounded-full" 
                                  style={{ width: `${predictionData.confidence * 100}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Chart */}
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart
                            data={chartData}
                            margin={{
                              top: 5,
                              right: 30,
                              left: 20,
                              bottom: 5,
                            }}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="date" 
                              tick={{ fontSize: 12 }}
                              tickFormatter={(value) => {
                                const date = new Date(value);
                                return `${date.getMonth() + 1}/${date.getDate()}`;
                              }}
                            />
                            <YAxis 
                              tick={{ fontSize: 12 }}
                              domain={['auto', 'auto']}
                              tickFormatter={(value) => `$${value}`} 
                            />
                            <Tooltip 
                              formatter={(value) => [`$${value}`, 'Price']}
                              labelFormatter={(label) => `Date: ${label}`}
                            />
                            <Legend />
                            <Line
                              type="monotone"
                              dataKey="price"
                              name="Historical Price"
                              stroke="#4F46E5"
                              activeDot={{ r: 8 }}
                              strokeWidth={2}
                              dot={{ r: 1 }}
                              isAnimationActive={true}
                              connectNulls={true}
                            />
                            <Line
                              type="monotone"
                              dataKey="price"
                              name="Predicted Price"
                              stroke="#D946EF"
                              strokeDasharray="5 5"
                              strokeWidth={2}
                              dot={{ r: 1 }}
                              isAnimationActive={true}
                              connectNulls={true}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                      
                      {/* Legend */}
                      <div className="mt-3 flex space-x-4 justify-center">
                        <div className="flex items-center">
                          <span className="h-3 w-3 bg-indigo-600 rounded-full mr-1"></span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">Historical</span>
                        </div>
                        <div className="flex items-center">
                          <span className="h-3 w-3 bg-purple-600 rounded-full mr-1"></span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">Predicted</span>
                        </div>
                      </div>
                      
                      {/* Prediction disclaimer */}
                      <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center italic">
                        Predictions are based on historical data and should not be used as the sole basis for investment decisions.
                        Past performance is not indicative of future results.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-10 flex items-center justify-center">
                    <p className="text-gray-500 dark:text-gray-400">
                      Select a stock to view its chart and price prediction
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
} 