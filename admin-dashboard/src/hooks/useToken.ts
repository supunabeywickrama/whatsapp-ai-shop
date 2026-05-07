'use client';

import { useEffect, useState } from 'react';

export function useToken(): string | null {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    setToken(localStorage.getItem('admin_token'));
  }, []);
  return token;
}
