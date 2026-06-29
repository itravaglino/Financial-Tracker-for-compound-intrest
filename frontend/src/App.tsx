import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import Analysis from './pages/Analysis';
import Trading from './pages/Trading';
import Alerts from './pages/Alerts';
import CompoundInterest from './pages/CompoundInterest';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
    </div>
  );
  return user ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="analysis" element={<Analysis />} />
        <Route path="trading" element={<Trading />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="compound" element={<CompoundInterest />} />
      </Route>
    </Routes>
  );
}
