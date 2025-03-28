'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface AuthCheckProps {
  children: React.ReactNode;
}

export default function AuthCheck({ children }: AuthCheckProps) {
  const router = useRouter();
  
  useEffect(() => {
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const userId = localStorage.getItem('userId');
    
    // If not logged in, redirect to login page
    if (!isLoggedIn || !userId) {
      router.push('/auth?type=login');
    }
  }, [router]);
  
  return <>{children}</>;
} 