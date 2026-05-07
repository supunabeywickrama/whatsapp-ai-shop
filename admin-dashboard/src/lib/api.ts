const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export async function api<T = unknown>(
  path: string,
  init: RequestInit = {},
  token?: string,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
}
