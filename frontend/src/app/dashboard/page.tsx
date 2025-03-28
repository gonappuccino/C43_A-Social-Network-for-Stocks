// filepath: c:\Users\jsdan\OneDrive - University of Toronto\CSCC43\C43_A-Social-Network-for-Stocks\frontend\src\app\dashboard\page.tsx
'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  Portfolio, 
  PortfolioView, 
  ApiPortfolio, 
  calculatePortfolioValue, 
  toPortfolioView 
} from '@/models/PortfolioModels';
import AuthCheck from '../../components/AuthCheck';

// Define interfaces for our data types
interface StockList {
  id: number;
  name: string;
  isPublic: boolean;
  stockCount: number;
  visibility?: string;
}

interface FriendRequest {
  id: number;
  username: string;
  date: string;
}

// UI-specific Portfolio interface that extends PortfolioView
interface DashboardPortfolio extends PortfolioView {
  cash: number;
  change: number;
  stockCount: number;
}

export default function Dashboard() {
  const router = useRouter();
  const [portfolios, setPortfolios] = useState<DashboardPortfolio[]>([]);
  const [stockLists, setStockLists] = useState<StockList[]>([]);
  const [activity, setActivity] = useState<any[]>([]);
  const [friendRequests, setFriendRequests] = useState<FriendRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);
  const [showNewPortfolioModal, setShowNewPortfolioModal] = useState(false);
  const [showNewStockListModal, setShowNewStockListModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [initialCash, setInitialCash] = useState('1000');
  const [newStockListName, setNewStockListName] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  
  // Calculate total portfolio value
  const totalPortfolioValue = portfolios.reduce((total, portfolio) => total + portfolio.value, 0);
  
  // Format date for display
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  useEffect(() => {
    // Check if user is logged in
    const storedUserId = localStorage.getItem('userId');
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    
    if (!storedUserId || !isLoggedIn) {
      router.push('/auth?type=login');
      return;
    }
    
    setUserId(storedUserId);
    
    // Fetch data from backend
    fetchUserData(storedUserId);
  }, [router]);
  
  const fetchUserData = async (userId: string) => {
    setIsLoading(true);
    
    try {
      // Get API URL from environment variable or fallback to localhost:5001
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      
      // Mock portfolio data instead of fetching from backend
      const mockPortfoliosData = [
        {
          portfolio_id: 1,
          portfolio_name: "Growth Portfolio",
          user_id: parseInt(userId),
          cash_balance: 2500,
          created_at: new Date().toISOString(),
          stocks: [
            { symbol: "AAPL", num_shares: 10 },
            { symbol: "MSFT", num_shares: 5 },
            { symbol: "GOOGL", num_shares: 2 }
          ]
        },
        {
          portfolio_id: 2,
          portfolio_name: "Dividend Portfolio",
          user_id: parseInt(userId),
          cash_balance: 1800,
          created_at: new Date().toISOString(),
          stocks: [
            { symbol: "JNJ", num_shares: 8 },
            { symbol: "PG", num_shares: 12 },
            { symbol: "KO", num_shares: 20 }
          ]
        }
      ];
      
      // Transform portfolio data using a manually defined function to avoid TypeScript issues
      const transformPortfolios = (apiPortfolios: any): DashboardPortfolio[] => {
        // Check if apiPortfolios is an array, if not convert or create an empty array
        const portfoliosArray = Array.isArray(apiPortfolios) ? apiPortfolios : (apiPortfolios ? [apiPortfolios] : []);
        
        return portfoliosArray.map((port: any) => ({
          ...toPortfolioView(port),
          cash: port.cash_balance || 0,
          stockCount: port.stocks?.length || 0,
          change: Math.random() * 10 - 5 // Random change between -5% and 5% for mock data
        }));
      };
      
      console.log('Mock Portfolios data:', mockPortfoliosData);
      setPortfolios(transformPortfolios(mockPortfoliosData));
      
      // Fetch stock lists
      const stockListsResponse = await fetch(`${apiUrl}/view_accessible_stock_lists?user_id=${userId}`);
      const stockListsData = await stockListsResponse.json();
      
      // Transform stock lists data
      const transformedStockLists: StockList[] = stockListsData.map((list: any) => ({
        id: list.stocklist_id,
        name: `Stock List ${list.stocklist_id}`, // You may want to add names in your backend
        isPublic: list.is_public,
        stockCount: 0, // You would need to fetch this separately
        visibility: list.visibility
      }));
      
      setStockLists(transformedStockLists);
      
      // Fetch incoming friend requests
      const friendRequestsResponse = await fetch(`${apiUrl}/view_incoming_requests?user_id=${userId}`);
      const friendRequestsData = await friendRequestsResponse.json();
      
      // Transform friend requests data
      const transformedRequests: FriendRequest[] = friendRequestsData.map((req: any) => ({
        id: req[0],
        username: `User ${req[1]}`, // You would need to fetch usernames
        date: new Date().toISOString() // You might want to add timestamps to requests
      }));
      
      setFriendRequests(transformedRequests);
      
    } catch (error) {
      console.error('Error fetching user data:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const createNewPortfolio = async () => {
    if (!userId) return;
    
    try {
      console.log("Creating portfolio with user_id:", userId, "and cash:", initialCash);
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      const response = await fetch(`${apiUrl}/create_portfolio`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: parseInt(userId), // Convert to integer
          initial_cash: parseFloat(initialCash)
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Portfolio created:", data);
        // Refetch portfolios to show the new one
        fetchUserData(userId);
        setShowNewPortfolioModal(false);
        setNewPortfolioName('');
        setInitialCash('1000');
      } else {
        const errorData = await response.json();
        console.error("Failed to create portfolio:", errorData);
      }
    } catch (error) {
      console.error('Error creating portfolio:', error);
    }
  };

  const handleAcceptFriendRequest = async (requestId: number) => {
    if (!userId) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      const response = await fetch(`${apiUrl}/accept_friend_request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request_id: requestId
        }),
      });
      
      if (response.ok) {
        // Refetch friend requests
        fetchUserData(userId);
      }
    } catch (error) {
      console.error('Error accepting friend request:', error);
    }
  };

  const handleRejectFriendRequest = async (requestId: number) => {
    if (!userId) return;
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      const response = await fetch(`${apiUrl}/reject_friend_request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request_id: requestId
        }),
      });
      
      if (response.ok) {
        // Refetch friend requests
        fetchUserData(userId);
      }
    } catch (error) {
      console.error('Error rejecting friend request:', error);
    }
  };

  // Fix the createNewStockList function
  const createNewStockList = async () => {
    if (!userId) return;
    
    try {
      console.log("Creating stock list with creator_id:", userId, "and is_public:", isPublic);
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      const response = await fetch(`${apiUrl}/create_stock_list`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          creator_id: parseInt(userId), // Convert to integer
          is_public: isPublic
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("Stock list created:", data);
        // Refetch stock lists to show the new one
        fetchUserData(userId);
        setShowNewStockListModal(false);
        setNewStockListName('');
        setIsPublic(false);
      } else {
        const errorData = await response.json();
        console.error("Failed to create stock list:", errorData);
      }
    } catch (error) {
      console.error('Error creating stock list:', error);
    }
  };

  
  if (isLoading) {
    return (
      <AuthCheck>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <Navbar />
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
            <p className="text-lg text-gray-500 dark:text-gray-400">Loading your dashboard...</p>
          </div>
        </div>
      </AuthCheck>
    );
  }
  
  return (
    <AuthCheck>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navbar />
        <main className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
            
            {/* Quick stats section */}
            <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Portfolio Value</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">${totalPortfolioValue.toLocaleString()}</dd>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Portfolios</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">{portfolios.length}</dd>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Stock Lists</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">{stockLists.length}</dd>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Friend Requests</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">{friendRequests.length}</dd>
                </div>
              </div>
            </div>
            
            {/* Portfolio summary section */}
            <div className="mt-8">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">Your Portfolios</h2>
                <Link href="/portfolios" className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
                  View all
                </Link>
              </div>
              <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {portfolios.length > 0 ? (
                  portfolios.map((portfolio) => (
                    <div key={portfolio.id} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                      <div className="px-4 py-5 sm:p-6">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">{portfolio.name}</h3>
                        <div className="mt-3 flex items-end justify-between">
                          <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                            ${(portfolio.value || 0).toLocaleString()}
                          </p>
                          <p className={`${portfolio.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'} flex items-center text-sm font-medium`}>
                            <span>
                              {portfolio.change >= 0 ? '↑' : '↓'} {Math.abs(portfolio.change).toFixed(2)}%
                            </span>
                          </p>
                        </div>
                        <div className="mt-4">
                          <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400">
                            <p>{portfolio.stockCount} stocks</p>
                            <p>Cash: ${(portfolio.cash || 0).toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="mt-4">
                          <Link 
                            href={`/portfolios/${portfolio.id}`}
                            className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                          >
                            View details →
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-3 text-center py-10">
                    <p className="text-gray-500 dark:text-gray-400">You don't have any portfolios yet. Create one to get started!</p>
                  </div>
                )}
                <div className="bg-gray-50 dark:bg-gray-900 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 flex items-center justify-center">
                  <button
                    onClick={() => setShowNewPortfolioModal(true)}
                    className="flex items-center justify-center text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                  >
                    <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create New Portfolio
                  </button>
                </div>
              </div>
            </div>
            
            {/* Stock lists section */}
            <div className="mt-8">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">Your Stock Lists</h2>
                <Link href="/stocklists" className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
                  View all
                </Link>
              </div>
              <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {stockLists.length > 0 ? (
                  stockLists.map((list) => (
                    <div key={list.id} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                      <div className="px-4 py-5 sm:p-6">
                        <div className="flex items-center justify-between">
                          <h3 className="text-lg font-medium text-gray-900 dark:text-white">{list.name}</h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${list.isPublic ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'}`}>
                            {list.isPublic ? 'Public' : 'Private'}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{list.stockCount} stocks</p>
                        {list.visibility === 'shared' && (
                          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Shared with friends</p>
                        )}
                        <div className="mt-4">
                          <Link 
                            href={`/stocklists/${list.id}`}
                            className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                          >
                            View details →
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-3 text-center py-10">
                    <p className="text-gray-500 dark:text-gray-400">You don't have any stock lists yet. Create one to get started!</p>
                  </div>
                )}
                <div className="bg-gray-50 dark:bg-gray-900 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 flex items-center justify-center">
                  <button
                    onClick={() => setShowNewStockListModal(true)}
                    className="flex items-center justify-center text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                  >
                    <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create New Stock List
                  </button>
                </div>
              </div>
            </div>
            
            {/* Friend requests section */}
            {friendRequests.length > 0 && (
              <div className="mt-8">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900 dark:text-white">Friend Requests</h2>
                  <Link href="/friends" className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400">
                    View all friends
                  </Link>
                </div>
                <div className="mt-4 bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                  <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                    {friendRequests.map((request) => (
                      <li key={request.id}>
                        <div className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                                <span className="text-gray-800 dark:text-gray-200 font-medium text-sm">
                                  {request.username.charAt(0).toUpperCase()}
                                </span>
                              </div>
                              <div className="ml-4">
                                <p className="text-sm font-medium text-gray-900 dark:text-white">
                                  {request.username}
                                </p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                  {formatDate(request.date)}
                                </p>
                              </div>
                            </div>
                            <div className="flex space-x-2">
                              <button 
                                onClick={() => handleAcceptFriendRequest(request.id)}
                                className="px-4 py-2 text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                              >
                                Accept
                              </button>
                              <button 
                                onClick={() => handleRejectFriendRequest(request.id)}
                                className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
                              >
                                Decline
                              </button>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
      
      {/* New Portfolio Modal */}
      {showNewPortfolioModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Create New Portfolio</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Initial Cash Balance
                </label>
                <input
                  type="number"
                  value={initialCash}
                  onChange={(e) => setInitialCash(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>
            <div className="mt-5 sm:mt-6 flex space-x-2">
              <button
                type="button"
                onClick={() => setShowNewPortfolioModal(false)}
                className="inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={createNewPortfolio}
                className="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* New Stock List Modal */}
      {showNewStockListModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Create New Stock List</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isPublic"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="isPublic" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                  Make this list public
                </label>
              </div>
            </div>
            <div className="mt-5 sm:mt-6 flex space-x-2">
              <button
                type="button"
                onClick={() => setShowNewStockListModal(false)}
                className="inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={createNewStockList}
                className="inline-flex justify-center w-full rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </AuthCheck>
  );
}
