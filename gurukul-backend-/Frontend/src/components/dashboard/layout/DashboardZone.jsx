import React from 'react';

const DashboardZone = ({ children, cols = 'lg:col-span-4', className = '' }) => {
  return (
    <div className={`space-y-6 ${cols} ${className}`}>
      {children}
    </div>
  );
};

export default DashboardZone;
