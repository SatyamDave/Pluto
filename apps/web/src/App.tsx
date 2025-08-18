import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PostHogProvider } from 'posthog-js/react';
import posthog from 'posthog-js';

// Components
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Pricing from './pages/Pricing';
import Backtest from './pages/Backtest';
import Trading from './pages/Trading';
import Profile from './pages/Profile';

// Initialize PostHog
posthog.init('phc_your_key_here', {
  api_host: 'https://app.posthog.com',
});

const ProtectedRoute: React.FC<{ children: React.ReactNode; requiredTier?: string }> = ({ 
  children, 
  requiredTier = 'learner' 
}) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const tierHierarchy = { learner: 0, pro: 1, quant: 2, enterprise: 3 };
  const userTierLevel = tierHierarchy[user.tier as keyof typeof tierHierarchy] || 0;
  const requiredTierLevel = tierHierarchy[requiredTier as keyof typeof tierHierarchy] || 0;

  if (userTierLevel < requiredTierLevel) {
    return <Navigate to="/pricing" replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <PostHogProvider client={posthog}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <AuthProvider>
          <Router>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/backtest" 
                element={
                  <ProtectedRoute>
                    <Backtest />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/trading" 
                element={
                  <ProtectedRoute requiredTier="pro">
                    <Trading />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <Profile />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </Router>
        </AuthProvider>
      </ConfigProvider>
    </PostHogProvider>
  );
};

export default App;
