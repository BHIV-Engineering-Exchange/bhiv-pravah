import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { CheckCircle, XCircle, AlertTriangle, Database } from 'lucide-react';

export default function DatabaseStatus() {
  const [status, setStatus] = useState('checking');
  const [details, setDetails] = useState(null);

  useEffect(() => {
    checkDatabaseStatus();
  }, []);

  const checkDatabaseStatus = async () => {
    try {
      setStatus('checking');
      
      // Test basic connection
      const { data, error } = await supabase
        .from('students')
        .select('count', { count: 'exact', head: true });

      if (error) {
        setStatus('error');
        setDetails({
          message: 'Database connection failed',
          error: error.message,
          suggestion: 'Check Supabase configuration and RLS policies'
        });
        return;
      }

      // Test if we can insert (this will fail if RLS policies are wrong)
      const testUserId = 'test-user-' + Date.now();
      const { error: insertError } = await supabase
        .from('students')
        .insert([{
          user_id: testUserId,
          name: 'Test User',
          email: 'test@example.com',
          student_id: 'TEST123'
        }]);

      if (insertError && insertError.message.includes('row-level security policy')) {
        setStatus('warning');
        setDetails({
          message: 'Database connected but RLS policies need setup',
          error: insertError.message,
          suggestion: 'Run the SQL script from src/sql/fix_rls_policies.sql in Supabase'
        });
        return;
      }

      // Clean up test record if it was inserted
      if (!insertError) {
        await supabase
          .from('students')
          .delete()
          .eq('user_id', testUserId);
      }

      setStatus('success');
      setDetails({
        message: 'Database is properly configured',
        suggestion: 'All systems ready for assignment data storage'
      });

    } catch (error) {
      setStatus('error');
      setDetails({
        message: 'Unexpected database error',
        error: error.message,
        suggestion: 'Check network connection and Supabase status'
      });
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-orange-400" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-400" />;
      default:
        return <Database className="h-5 w-5 text-blue-400 animate-pulse" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'border-green-500/30 bg-green-500/10';
      case 'warning':
        return 'border-orange-500/30 bg-orange-500/10';
      case 'error':
        return 'border-red-500/30 bg-red-500/10';
      default:
        return 'border-blue-500/30 bg-blue-500/10';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'success':
        return 'Database Ready';
      case 'warning':
        return 'Database Needs Setup';
      case 'error':
        return 'Database Error';
      default:
        return 'Checking Database...';
    }
  };

  return (
    <div className={`p-4 rounded-lg border ${getStatusColor()}`}>
      <div className="flex items-center gap-3 mb-2">
        {getStatusIcon()}
        <span className="font-medium text-white">{getStatusText()}</span>
      </div>
      
      {details && (
        <div className="space-y-2">
          <div className="text-sm text-white/80">
            {details.message}
          </div>
          
          {details.error && (
            <div className="text-xs text-white/60 bg-white/5 p-2 rounded">
              Error: {details.error}
            </div>
          )}
          
          <div className="text-xs text-white/70">
            💡 {details.suggestion}
          </div>
        </div>
      )}
      
      <button
        onClick={checkDatabaseStatus}
        className="mt-3 text-xs px-3 py-1 bg-white/10 hover:bg-white/20 text-white rounded transition-colors"
      >
        Recheck Status
      </button>
    </div>
  );
}
