import { Navigate, Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import PropertyPage from './pages/PropertyPage';
import OwnerDashboard from './pages/OwnerDashboard';
import SuperAdminDashboard from './pages/SuperAdminDashboard';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/stays/:id" element={<PropertyPage />} />
      <Route path="/owner" element={<OwnerDashboard />} />
      <Route path="/super-admin" element={<SuperAdminDashboard />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}