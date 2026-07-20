import React from 'react';
import { AlertTriangle, Info, Zap, ShieldAlert } from 'lucide-react';

const AlertFeed = ({ alerts }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'anomaly': return <ShieldAlert size={18} className="text-red-500" />;
      case 'pattern': return <Zap size={18} className="text-yellow-500" />;
      case 'risk': return <AlertTriangle size={18} className="text-orange-500" />;
      default: return <Info size={18} className="text-blue-500" />;
    }
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden h-full">
      <div className="p-5 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
        <h3 className="font-bold text-white tracking-tight">TANTRA Signal Feed</h3>
        <span className="text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 uppercase">Live</span>
      </div>
      
      <div className="divide-y divide-white/5 max-h-[500px] overflow-y-auto">
        {alerts.map((alert, idx) => (
          <div key={idx} className="p-4 hover:bg-white/5 transition-colors group cursor-pointer">
            <div className="flex gap-4">
              <div className="mt-1">{getIcon(alert.type)}</div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-1">
                  <h4 className="text-sm font-semibold text-white group-hover:text-accent transition-colors">{alert.title}</h4>
                  <span className="text-[10px] text-gray-500 font-mono">{alert.time}</span>
                </div>
                <p className="text-xs text-gray-400 mb-2 leading-relaxed">{alert.message}</p>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-gray-600 bg-black/40 px-1.5 py-0.5 rounded border border-white/5">
                    ID: {alert.trace_id}
                  </span>
                  <span className={`text-[10px] font-bold uppercase ${alert.priority === 'High' ? 'text-red-500' : 'text-gray-500'}`}>
                    {alert.priority} Priority
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="p-4 bg-white/[0.01] border-t border-white/5">
        <button className="w-full py-2 text-xs font-bold text-gray-500 hover:text-white transition-colors uppercase tracking-widest">
          View All Signals
        </button>
      </div>
    </div>
  );
};

export default AlertFeed;
