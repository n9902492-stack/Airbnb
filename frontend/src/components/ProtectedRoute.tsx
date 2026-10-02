import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { authStore, type UserRole } from '../lib/auth';

export default function ProtectedRoute({
  children,
  roles,
}: {
  children: ReactNode;
  roles?: UserRole[];
}) {
  const token = authStore.getToken();
  const user = authStore.getUser();

  if (!token || !user) {
    return <Navigate to="/auth" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
