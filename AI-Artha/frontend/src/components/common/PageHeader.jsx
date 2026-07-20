import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import Button from './Button';

const PageHeader = ({
  title,
  description,
  backUrl,
  action,
  children,
}) => {
  const navigate = useNavigate();

  return (
    <div className="mb-6">
      {backUrl && (
        <button
          onClick={() => navigate(backUrl)}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">Back</span>
        </button>
      )}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{title}</h1>
          {description && (
            <p className="text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        {action && (
          <div className="flex items-center gap-3">
            {action}
          </div>
        )}
        {children}
      </div>
    </div>
  );
};

export default PageHeader;
