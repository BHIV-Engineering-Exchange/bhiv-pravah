import React from 'react';

const DashboardGrid = ({ children, className = '' }) => {
  return (
    <div className={`grid grid-cols-1 lg:grid-cols-12 gap-6 w-full ${className}`}>
      {children}
    </div>
  );
};

export default DashboardGrid;
