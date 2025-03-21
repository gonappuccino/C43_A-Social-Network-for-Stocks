'use client';

import { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import Link from 'next/link';

// Mock data for demonstration
const mockPortfolios = [
  { id: 1, name: 'Main Portfolio', value: 25431.78, change: 2.4, stocks: 8, cash: 1520.43 },
  { id: 2, name: 'Retirement', value: 45128.91, change: -0.7, stocks: 12, cash: 2100.00 },
  { id: 3, name: 'Tech Stocks', value: 12890.55, change: 5.2, stocks: 5, cash: 500.20 },
];

const mockStockLists = [
  { id: 1, name: 'Watchlist', stockCount: 12, isPublic: false },
  { id: 2, name: 'Tech Giants', stockCount: 5, isPublic: true, reviewCount: 8 },
  { id: 3, name: 'Dividend Stocks', stockCount: 7, isPublic: false, sharedWith: 2 },
];

const mockActivity = [
  { id: 1, type: 'purchase', symbol: 'AAPL', shares: 5, price: 189.84, date: '2025-03-20T14:32:00Z' },
  { id: 2, type: 'sale', symbol: 'MSFT', shares: 3, price: 421.55, date: '2025-03-19T10:15:00Z' },
  { id: 3, type: 'friend_request', from: 'JaneDoe', status: 'pending', date: '2025-03-18T08:45:00Z' },
  { id: 4, type: 'review', stockList: 'Tech Giants', from: 'TechInvestor', date: '2025-03-17T16:20:00Z' },
  { id: 5, type: 'deposit', amount: 1000, portfolio: 'Main Portfolio', date: '2025-03-15T12:00:00Z' },
];

const mockFriendRequests = [
  { id: 1, username: 'JaneDoe', date: '2025-03-18T08:45:00Z' },
  { id: 2, username: 'StockGuru42', date: '2025-03-16T14:20:00Z' },
];

export default function Dashboard() {
  // We would fetch real data from API in a real application
  const [portfolios, setPortfolios] = useState(mockPortfolios);
  const [stockLists, setStockLists] = useState(mockStockLists);
  const [activity, setActivity] = useState(mockActivity);
  const [friendRequests, setFriendRequests] = useState(mockFriendRequests);
  
  // Calculate total portfolio value
  const totalPortfolioValue = portfolios.reduce((total, portfolio) => total + portfolio.value, 0);
  
  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
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
                {portfolios.map((portfolio) => (
                  <div key={portfolio.id} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                    <div className="px-4 py-5 sm:p-6">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">{portfolio.name}</h3>
                      <div className="mt-3 flex items-end justify-between">
                        <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                          ${portfolio.value.toLocaleString()}
                        </p>
                        <p className={`${portfolio.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'} flex items-center text-sm font-medium`}>
                          <span>
                            {portfolio.change >= 0 ? '↑' : '↓'} {Math.abs(portfolio.change)}%
                          </span>
                        </p>
                      </div>
                      <div className="mt-4">
                        <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400">
                          <p>{portfolio.stocks} stocks</p>
                          <p>Cash: ${portfolio.cash.toLocaleString()}</p>
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
                ))}
                <div className="bg-gray-50 dark:bg-gray-900 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 flex items-center justify-center">
                  <Link
                    href="/portfolios/create"
                    className="flex items-center justify-center text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                  >
                    <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create New Portfolio
                  </Link>
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
                {stockLists.map((list) => (
                  <div key={list.id} className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                    <div className="px-4 py-5 sm:p-6">
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">{list.name}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${list.isPublic ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'}`}>
                          {list.isPublic ? 'Public' : 'Private'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{list.stockCount} stocks</p>
                      {list.reviewCount && (
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{list.reviewCount} reviews</p>
                      )}
                      {list.sharedWith && (
                        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Shared with {list.sharedWith} friends</p>
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
                ))}
                <div className="bg-gray-50 dark:bg-gray-900 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 flex items-center justify-center">
                  <Link
                    href="/stocklists/create"
                    className="flex items-center justify-center text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                  >
                    <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create New Stock List
                  </Link>
                </div>
              </div>
            </div>
            
            {/* Activity section */}
            <div className="mt-8">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">Recent Activity</h2>
              </div>
              <div className="mt-4 bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                  {activity.map((item) => (
                    <li key={item.id}>
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            {item.type === 'purchase' && (
                              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                                <svg className="h-5 w-5 text-green-800 dark:text-green-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                                </svg>
                              </div>
                            )}
                            {item.type === 'sale' && (
                              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
                                <svg className="h-5 w-5 text-red-800 dark:text-red-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                                </svg>
                              </div>
                            )}
                            {item.type === 'friend_request' && (
                              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                <svg className="h-5 w-5 text-blue-800 dark:text-blue-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                              </div>
                            )}
                            {item.type === 'review' && (
                              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                                <svg className="h-5 w-5 text-purple-800 dark:text-purple-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                              </div>
                            )}
                            {item.type === 'deposit' && (
                              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center">
                                <svg className="h-5 w-5 text-yellow-800 dark:text-yellow-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                                </svg>
                              </div>
                            )}
                            <div className="ml-4">
                              <p className="text-sm font-medium text-gray-900 dark:text-white">
                                {item.type === 'purchase' && `Purchased ${item.shares} shares of ${item.symbol} at $${item.price}`}
                                {item.type === 'sale' && `Sold ${item.shares} shares of ${item.symbol} at $${item.price}`}
                                {item.type === 'friend_request' && `Friend request from ${item.from}`}
                                {item.type === 'review' && `${item.from} reviewed your "${item.stockList}" list`}
                                {item.type === 'deposit' && `Deposited $${item.amount} to ${item.portfolio}`}
                              </p>
                              <p className="text-sm text-gray-500 dark:text-gray-400">
                                {formatDate(item.date)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
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
                              <button className="px-4 py-2 text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                                Accept
                              </button>
                              <button className="px-4 py-2 text-sm font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600">
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
    </>
  );
} 