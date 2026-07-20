import React from 'react';

const DashboardSection = ({ title, children, className = '' }) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {title && (
        <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest ml-1">
          {title}
        </h4>
      )}
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );
};

export default DashboardSection;
