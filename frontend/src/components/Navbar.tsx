'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
  // Check login status on component mount and when pathname changes
  useEffect(() => {
    // Check localStorage for login status
    const loginStatus = localStorage.getItem('isLoggedIn') === 'true';
    setIsLoggedIn(loginStatus);
  }, [pathname]);
  
  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };
  
  const handleSignOut = () => {
    // Clear user data from localStorage
    localStorage.removeItem('userId');
    localStorage.removeItem('isLoggedIn');
    setIsLoggedIn(false);
    
    // Redirect to home page
    router.push('/');
  };

  return (
    <nav className="bg-white dark:bg-gray-900 border-b dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                StockSocial
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {isLoggedIn && (
                <>
                  <Link href="/dashboard" className={`${pathname === '/dashboard' ? 'border-indigo-500 text-gray-900 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-200'} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}>
                    Dashboard
                  </Link>
                  <Link href="/portfolios" className={`${pathname === '/portfolios' ? 'border-indigo-500 text-gray-900 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-200'} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}>
                    Portfolios
                  </Link>
                  <Link href="/stocklists" className={`${pathname === '/stocklists' ? 'border-indigo-500 text-gray-900 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-200'} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}>
                    Stock Lists
                  </Link>
                  <Link href="/friends" className={`${pathname === '/friends' ? 'border-indigo-500 text-gray-900 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-200'} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}>
                    Friends
                  </Link>
                </>
              )}
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            {isLoggedIn ? (
              <div className="flex items-center">
                <Link href="/dashboard" className="mr-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                  My Page
                </Link>
                <button onClick={handleSignOut} className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link href="/auth?type=login" className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
                  Sign In
                </Link>
                <Link href="/auth?type=register" className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                  Sign Up
                </Link>
              </div>
            )}
          </div>
          <div className="-mr-2 flex items-center sm:hidden">
            <button onClick={toggleMenu} className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500">
              <span className="sr-only">Open main menu</span>
              {isMenuOpen ? (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {isLoggedIn && (
              <>
                <Link href="/dashboard" className={`${pathname === '/dashboard' ? 'bg-indigo-50 border-indigo-500 text-indigo-700 dark:bg-gray-800 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-white'} block pl-3 pr-4 py-2 border-l-4 text-base font-medium`}>
                  Dashboard
                </Link>
                <Link href="/portfolios" className={`${pathname === '/portfolios' ? 'bg-indigo-50 border-indigo-500 text-indigo-700 dark:bg-gray-800 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-white'} block pl-3 pr-4 py-2 border-l-4 text-base font-medium`}>
                  Portfolios
                </Link>
                <Link href="/stocklists" className={`${pathname === '/stocklists' ? 'bg-indigo-50 border-indigo-500 text-indigo-700 dark:bg-gray-800 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-white'} block pl-3 pr-4 py-2 border-l-4 text-base font-medium`}>
                  Stock Lists
                </Link>
                <Link href="/friends" className={`${pathname === '/friends' ? 'bg-indigo-50 border-indigo-500 text-indigo-700 dark:bg-gray-800 dark:text-white' : 'border-transparent text-gray-500 dark:text-gray-300 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-white'} block pl-3 pr-4 py-2 border-l-4 text-base font-medium`}>
                  Friends
                </Link>
              </>
            )}
          </div>
          <div className="pt-4 pb-3 border-t border-gray-200 dark:border-gray-700">
            {isLoggedIn ? (
              <div className="space-y-1">
                <Link href="/dashboard" className="block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-white">
                  My Page
                </Link>
                <button onClick={handleSignOut} className="block w-full text-left pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-white">
                  Sign out
                </button>
              </div>
            ) : (
              <div className="space-y-1 px-4">
                <Link href="/auth?type=login" className="block text-base font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300">
                  Sign In
                </Link>
                <Link href="/auth?type=register" className="mt-1 block px-4 py-2 text-center border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-indigo-600 hover:bg-indigo-700">
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
