'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const res = await api<{ token: string }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('admin_token', res.token);
      router.push('/');
    } catch (err) {
      setError('Invalid credentials');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="container max-w-sm py-24">
      <h1 className="text-2xl font-bold mb-6">Sign in</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <input
          type="email"
          placeholder="Email"
          className="w-full rounded-md border bg-background px-3 py-2"
          value={email} onChange={(e) => setEmail(e.target.value)} required
        />
        <input
          type="password"
          placeholder="Password"
          className="w-full rounded-md border bg-background px-3 py-2"
          value={password} onChange={(e) => setPassword(e.target.value)} required
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <button
          type="submit" disabled={busy}
          className="w-full rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </main>
  );
}
