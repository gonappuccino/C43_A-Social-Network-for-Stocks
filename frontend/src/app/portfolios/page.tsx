'use client';

import { useState } from 'react';
import Navbar from '../../components/Navbar';
import Link from 'next/link';

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

export default function Portfolios() {
  const [portfolios, setPortfolios] = useState(mockPortfolios);
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [initialCash, setInitialCash] = useState('0');
  
  // Sort portfolios based on the selected field and direction
  const sortedPortfolios = [...portfolios].sort((a, b) => {
    let comparison = 0;
    
    if (sortField === 'name') {
      comparison = a.name.localeCompare(b.name);
    } else if (sortField === 'value') {
      comparison = a.value - b.value;
    } else if (sortField === 'change') {
      comparison = a.change - b.change;
    }
    
    return sortDirection === 'asc' ? comparison : -comparison;
  });
  
  // Handle sort toggle
  const handleSort = (field: string) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };
  
  // Handle create portfolio form submission
  const handleCreatePortfolio = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Generate a new ID (in a real app, this would come from the backend)
    const newId = Math.max(...portfolios.map(p => p.id)) + 1;
    
    // Create the new portfolio
    const newPortfolio = {
      id: newId,
      name: newPortfolioName,
      value: parseFloat(initialCash),
      change: 0,
      dailyChange: 0,
      stocks: [],
      cash: parseFloat(initialCash)
    };
    
    // Add to the list of portfolios
    setPortfolios([...portfolios, newPortfolio]);
    
    // Reset form and close modal
    setNewPortfolioName('');
    setInitialCash('0');
    setShowCreateModal(false);
  };
  
  // Delete a portfolio
  const handleDeletePortfolio = (id: number) => {
    // In a real app, we would call an API to delete the portfolio
    setPortfolios(portfolios.filter(p => p.id !== id));
  };
  
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <main className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Your Portfolios</h1>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md flex items-center hover:bg-indigo-700"
              >
                <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create Portfolio
              </button>
            </div>
            
            {/* Portfolio List */}
            <div className="mt-8 flex flex-col">
              <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
                  <div className="shadow overflow-hidden border-b border-gray-200 dark:border-gray-700 sm:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('name')}
                          >
                            <div className="flex items-center">
                              Portfolio Name
                              {sortField === 'name' && (
                                <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sortDirection === 'asc' ? "M19 9l-7 7-7-7" : "M5 15l7-7 7 7"} />
                                </svg>
                              )}
                            </div>
                          </th>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('value')}
                          >
                            <div className="flex items-center">
                              Current Value
                              {sortField === 'value' && (
                                <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sortDirection === 'asc' ? "M19 9l-7 7-7-7" : "M5 15l7-7 7 7"} />
                                </svg>
                              )}
                            </div>
                          </th>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSort('change')}
                          >
                            <div className="flex items-center">
                              Daily Change
                              {sortField === 'change' && (
                                <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sortDirection === 'asc' ? "M19 9l-7 7-7-7" : "M5 15l7-7 7 7"} />
                                </svg>
                              )}
                            </div>
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Holdings
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Cash Balance
                          </th>
                          <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {sortedPortfolios.map((portfolio) => (
                          <tr key={portfolio.id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                                    {portfolio.name}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900 dark:text-white">${portfolio.value.toLocaleString()}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className={`text-sm ${portfolio.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                                {portfolio.change >= 0 ? '+' : ''}{portfolio.change}% (${portfolio.dailyChange >= 0 ? '+' : ''}{portfolio.dailyChange.toLocaleString()})
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900 dark:text-white">{portfolio.stocks.length} stocks</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900 dark:text-white">${portfolio.cash.toLocaleString()}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <div className="flex justify-end space-x-3">
                                <Link href={`/portfolios/${portfolio.id}`} className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300">
                                  View
                                </Link>
                                <Link href={`/portfolios/${portfolio.id}/edit`} className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300">
                                  Edit
                                </Link>
                                <button 
                                  onClick={() => handleDeletePortfolio(portfolio.id)} 
                                  className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
      
      {/* Create Portfolio Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:max-w-lg sm:w-full sm:p-6">
            <div>
              <div className="mt-3 text-center sm:mt-5">
                <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                  Create New Portfolio
                </h3>
                <div className="mt-2">
                  <form onSubmit={handleCreatePortfolio} className="space-y-4">
                    <div>
                      <label htmlFor="portfolio-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 text-left">
                        Portfolio Name
                      </label>
                      <input
                        type="text"
                        name="portfolio-name"
                        id="portfolio-name"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        placeholder="My Portfolio"
                        value={newPortfolioName}
                        onChange={(e) => setNewPortfolioName(e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="initial-cash" className="block text-sm font-medium text-gray-700 dark:text-gray-300 text-left">
                        Initial Cash Balance ($)
                      </label>
                      <input
                        type="number"
                        name="initial-cash"
                        id="initial-cash"
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        placeholder="10000"
                        value={initialCash}
                        onChange={(e) => setInitialCash(e.target.value)}
                        min="0"
                        step="0.01"
                        required
                      />
                    </div>
                    <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                      <button
                        type="submit"
                        className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:col-start-2 sm:text-sm"
                      >
                        Create
                      </button>
                      <button
                        type="button"
                        className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:col-start-1 sm:text-sm dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
                        onClick={() => setShowCreateModal(false)}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
} 