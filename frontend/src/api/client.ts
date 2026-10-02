export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export async function refreshAccessToken(): Promise<string | null> {
  const response = await fetch(API_BASE_URL + '/auth/refresh', {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) return null;

  const data = (await response.json()) as { access_token: string };
  localStorage.setItem('nestora_access_token', data.access_token);
  return data.access_token;
}

export function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('nestora_access_token');
  if (!token) throw new Error('Please sign in first');
  return { Authorization: 'Bearer ' + token };
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
  });

  if (response.status === 401 && retry && path !== '/auth/refresh') {
    const token = await refreshAccessToken();
    if (token) {
      const headers = new Headers(options.headers ?? {});
      headers.set('Authorization', 'Bearer ' + token);
      return apiRequest<T>(path, { ...options, headers }, false);
    }
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error((data as { detail?: string }).detail ?? 'Something went wrong');
  }

  return data as T;
}

export async function uploadFileWithAuth<T>(
  path: string,
  file: File,
  fieldName = 'file',
): Promise<T> {
  let token = localStorage.getItem('nestora_access_token');
  if (!token) throw new Error('Please sign in first');

  const upload = () => {
    const body = new FormData();
    body.append(fieldName, file);
    return fetch(API_BASE_URL + path, {
      method: 'POST',
      credentials: 'include',
      headers: { Authorization: 'Bearer ' + token },
      body,
    });
  };

  let response = await upload();

  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      token = refreshed;
      response = await upload();
    }
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error((data as { detail?: string }).detail ?? 'Upload failed');
  }

  return data as T;
}
