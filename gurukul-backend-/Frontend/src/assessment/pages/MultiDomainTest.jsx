import { useAuth } from "../../contexts/AuthContext";
import MultiDomainAssignment from '../components/MultiDomainAssignment';
import { useNavigate } from 'react-router-dom';

export default function MultiDomainTest() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleComplete = (results) => {
    console.log('✅ Assessment completed!', results);
    // Navigate to dashboard or show results
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <MultiDomainAssignment
        userId={user?.id}
        userEmail={user?.email}
        onComplete={handleComplete}
      />
    </div>
  );
}
