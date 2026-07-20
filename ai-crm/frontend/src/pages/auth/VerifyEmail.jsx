import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail } from 'lucide-react';
import AuthLayout from '../../components/auth/AuthLayout';
import Button from '../../components/common/ui/Button';

/**
 * Email Verification Page
 * Note: Email verification is not currently implemented in the MongoDB backend.
 * This page informs users that they can proceed directly to login.
 */
const VerifyEmail = () => {
  const navigate = useNavigate();

  return (
    <AuthLayout>
      <div className="text-center space-y-6">
        <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
          <Mail className="w-8 h-8 text-primary" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-heading font-bold">Welcome!</h2>
          <p className="text-muted-foreground">
            Your account has been created successfully.
          </p>
          <p className="text-sm text-muted-foreground">
            Email verification is not required. You can proceed to login with your credentials.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={() => navigate('/auth/login')}
            className="gradient-primary"
          >
            Go to Login
          </Button>
        </div>
      </div>
    </AuthLayout>
  );
};

export default VerifyEmail;
