export type UserRole = 'user' | 'owner' | 'super_admin';

export type CurrentUser = {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
};

const TOKEN_KEY = 'nestora_access_token';
const USER_KEY = 'nestora_current_user';

export const authStore = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  setUser: (user: CurrentUser) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  getUser: (): CurrentUser | null => {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as CurrentUser;
    } catch {
      return null;
    }
  },
};

export function homeForRole(role: UserRole) {
  if (role === 'owner') return '/owner';
  if (role === 'super_admin') return '/super-admin';
  return '/user';
}
