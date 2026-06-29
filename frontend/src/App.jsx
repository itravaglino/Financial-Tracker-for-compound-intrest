import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Trading from './pages/Trading';
import Alerts from './pages/Alerts';
import StopLoss from './pages/StopLoss';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading"><div className="spinner" /></div>;
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="analysis" element={<Analysis />} />
            <Route path="trading" element={<Trading />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="stop-loss" element={<StopLoss />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
