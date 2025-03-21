# StockSocial - A Social Network for Stocks

A Next.js web application for CSCC43: Introduction to Databases project (Winter 2025).

## Project Overview

StockSocial is a social network platform that allows users to:
- Track portfolios of stocks
- Analyze and predict stock performance
- Create and share stock lists
- Connect with friends and share investment insights

## Project Structure

```
├── backend/               # Flask backend API
│   ├── launcher.py        # Server startup script
│   └── queries/           # SQL queries for PostgreSQL
│       ├── admin.py
│       ├── setup.py
│       ├── user.py
│       └── utils.py
└── frontend/              # Next.js frontend application
    ├── public/            # Static files
    └── src/               # Source code
        ├── app/           # Pages using App Router
        │   ├── auth/      # Authentication pages
        │   ├── dashboard/ # User dashboard
        │   ├── portfolios/# Portfolio management
        │   └── ...        # Other pages
        └── components/    # Reusable components
            ├── Navbar.tsx # Navigation component
            └── ...        # Other components
```

## Features

- **User Authentication**: Register, login, and logout
- **Portfolio Management**: Create, view, edit, and delete portfolios
- **Stock Trading**: Buy and sell stocks with real-time pricing
- **Stock Analysis**: Analyze historical performance and predict future trends
- **Social Features**: Friend requests, connections, and stock list sharing
- **Reviews**: Share and read reviews on public stock lists

## Getting Started

### Prerequisites

- Node.js (v16 or later)
- Python 3 (for backend)
- PostgreSQL database

### Running the Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Running the Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the Flask server:
   ```
   python launcher.py
   ```

## Database Schema

The application uses a PostgreSQL database with the following main tables:
- Users
- Portfolios
- PortfolioTransactions
- Stocks
- StockHistory
- StockLists
- Friends
- FriendRequests
- Reviews

## Project Status

This project is currently in development for CSCC43 course submission (due April 5, 2025).
