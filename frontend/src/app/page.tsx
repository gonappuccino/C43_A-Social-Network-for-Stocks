import Navbar from '../components/Navbar';
import Link from 'next/link';
import Image from 'next/image';

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="flex flex-col items-center">
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-b from-white to-indigo-50 dark:from-gray-900 dark:to-gray-800">
          <div className="container px-4 md:px-6 mx-auto flex flex-col items-center justify-center space-y-4 text-center">
            <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl/none">
              A Social Network for <span className="text-indigo-600 dark:text-indigo-400">Stock Investors</span>
            </h1>
            <p className="mx-auto max-w-[700px] text-gray-500 md:text-xl dark:text-gray-400">
              Track portfolios, analyze stocks, and connect with friends to make better investment decisions.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 mt-8">
              <Link href="/auth?type=register" className="inline-flex h-10 items-center justify-center rounded-md bg-indigo-600 px-8 text-sm font-medium text-white shadow transition-colors hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500">
                Get Started
              </Link>
              <Link href="/features" className="inline-flex h-10 items-center justify-center rounded-md border border-gray-200 bg-white px-8 text-sm font-medium shadow-sm transition-colors hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 dark:border-gray-800 dark:bg-gray-950 dark:hover:bg-gray-800 dark:hover:text-gray-50 dark:focus-visible:ring-gray-300">
                Learn More
              </Link>
            </div>
          </div>
        </section>

        <section className="w-full py-12 md:py-24 lg:py-32">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="grid gap-6 lg:grid-cols-3 lg:gap-12">
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="p-2 bg-indigo-100 rounded-full dark:bg-indigo-900/20">
                  <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold">Track Your Portfolios</h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Manage multiple portfolios, track performance, and analyze historical data to make informed decisions.
                </p>
              </div>
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="p-2 bg-indigo-100 rounded-full dark:bg-indigo-900/20">
                  <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold">Analyze Stock Performance</h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Use advanced analytics to predict future stock performance based on historical data.
                </p>
              </div>
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="p-2 bg-indigo-100 rounded-full dark:bg-indigo-900/20">
                  <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold">Connect with Friends</h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Share stock lists, request reviews, and collaborate with friends to improve your investment strategy.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t border-gray-200 dark:border-gray-800">
        <div className="container px-4 md:px-6 py-8 mx-auto">
          <div className="text-center text-gray-500 dark:text-gray-400">
            <p>&copy; 2025 StockSocial. All rights reserved.</p>
            <p className="mt-1 text-sm">A project for CSCC43: Introduction to Databases</p>
          </div>
        </div>
      </footer>
    </>
  );
}
