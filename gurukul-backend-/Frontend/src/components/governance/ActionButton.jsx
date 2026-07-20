import React from 'react';
import { ArrowRight } from 'lucide-react';

const ActionButton = ({ label, subLabel, onClick, icon: Icon, variant = 'primary' }) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return 'bg-red-500/10 border-red-500/30 text-red-500 hover:bg-red-500/20';
      case 'warning':
        return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500 hover:bg-yellow-500/20';
      case 'accent':
        return 'bg-accent/10 border-accent/30 text-accent hover:bg-accent/20';
      default:
        return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/20';
    }
  };

  return (
    <button 
      onClick={onClick}
      className={`group relative flex flex-col items-start w-full p-4 rounded-2xl border transition-all duration-300 transform hover:-translate-y-1 active:scale-95 ${getVariantStyles()}`}
    >
      <div className="flex justify-between items-center w-full mb-1">
        <div className="flex items-center gap-2">
          {Icon && <Icon size={18} />}
          <span className="font-bold text-sm uppercase tracking-wider">{label}</span>
        </div>
        <ArrowRight size={16} className="opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
      </div>
      
      {subLabel && (
        <span className="text-[10px] font-medium text-current/70 text-left">
          {subLabel}
        </span>
      )}

      {/* Glossy Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
    </button>
  );
};

export default ActionButton;
