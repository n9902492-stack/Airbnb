const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

type ApiOptions = RequestInit & {
  token?: string;
};

export async function apiRequest<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const { token, headers, ...requestOptions } = options;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? 'Something went wrong');
  }

  return response.json() as Promise<T>;
}
