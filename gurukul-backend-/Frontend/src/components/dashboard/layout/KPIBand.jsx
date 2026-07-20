import React from 'react';

const KPIBand = ({ children, className = '' }) => {
  return (
    <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 w-full mb-6 ${className}`}>
      {children}
    </div>
  );
};

export default KPIBand;
