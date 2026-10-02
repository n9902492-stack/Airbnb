import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import AddPropertyPage from './pages/AddPropertyPage';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import OwnerDashboard from './pages/OwnerDashboard';
import PropertyPage from './pages/PropertyPage';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import UserDashboard from './pages/UserDashboard';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/stays/:id" element={<PropertyPage />} />

      <Route
        path="/user"
        element={
          <ProtectedRoute roles={['user']}>
            <UserDashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/owner"
        element={
          <ProtectedRoute roles={['owner', 'super_admin']}>
            <OwnerDashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/owner/properties/new"
        element={
          <ProtectedRoute roles={['owner', 'super_admin']}>
            <AddPropertyPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/super-admin"
        element={
          <ProtectedRoute roles={['super_admin']}>
            <SuperAdminDashboard />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
