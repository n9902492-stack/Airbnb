import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import AddPropertyPage from './pages/AddPropertyPage';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import OwnerDashboard from './pages/OwnerDashboard';
import PropertyPage from './pages/PropertyPage';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import UserDashboard from './pages/UserDashboard';
import CheckoutPage from './pages/CheckoutPage';
import EditPropertyPage from './pages/EditPropertyPage';
import BookingMessagesPage from './pages/BookingMessagesPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/stays/:id" element={<PropertyPage />} />
      <Route
        path="/messages/:bookingId"
        element={
          <ProtectedRoute roles={['user', 'owner', 'super_admin']}>
            <BookingMessagesPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/checkout/:bookingId"
        element={
          <ProtectedRoute roles={['user']}>
            <CheckoutPage />
          </ProtectedRoute>
        }
      />

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
        path="/owner/properties/:propertyId/edit"
        element={
          <ProtectedRoute roles={['owner', 'super_admin']}>
            <EditPropertyPage />
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
