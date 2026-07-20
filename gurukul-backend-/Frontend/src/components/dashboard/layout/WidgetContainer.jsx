import React from 'react';

const WidgetContainer = ({ title, subTitle, children, actions, className = '', height = 'auto' }) => {
  return (
    <div 
      className={`glass-panel p-5 sm:p-6 rounded-3xl border border-white/10 bg-black/40 backdrop-blur-md transition-all duration-300 hover:border-white/15 flex flex-col justify-between ${className}`}
      style={{ height }}
    >
      {(title || subTitle || actions) && (
        <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-3">
          <div>
            {title && (
              <h3 className="font-bold text-white text-base tracking-tight leading-none">
                {title}
              </h3>
            )}
            {subTitle && (
              <p className="text-[10px] text-gray-500 font-semibold tracking-normal mt-1">
                {subTitle}
              </p>
            )}
          </div>
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      <div className="flex-1 w-full relative">
        {children}
      </div>
    </div>
  );
};

export default WidgetContainer;
