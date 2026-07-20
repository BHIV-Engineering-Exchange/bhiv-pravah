import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/MongoAuthContext';
import { Loader2 } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />;
  }

  const role = user?.role;
  const isCustomerPortal = location.pathname.startsWith('/customer-portal');

  // Customers are RESTRICTED to customer portal only
  if (role === 'customer' && !isCustomerPortal) {
    return <Navigate to="/customer-portal" replace />;
  }

  // Non-customers should NOT use the customer portal
  if (role !== 'customer' && isCustomerPortal) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
