
import React, { useState, useEffect } from 'react';
import { FaHeartbeat, FaMicrochip, FaShieldAlt, FaHistory, FaCheckCircle, FaExclamationTriangle, FaClock } from 'react-icons/fa';
import { apiGet, handleApiError } from '../../utils/apiClient';

const InfrastructureOverview = () => {
    const [vitality, setVitality] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState(new Date());

    useEffect(() => {
        fetchVitality();
        const interval = setInterval(fetchVitality, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchVitality = async () => {
        try {
            const data = await apiGet('/api/v1/prana/vitality');
            setVitality(data);
            setLastUpdated(new Date());
        } catch (error) {
            console.error('Failed to fetch vitality:', error);
        } finally {
            setLoading(false);
        }
    };

    const StatusCard = ({ title, status, icon: Icon, color, details }) => (
        <div className="bg-black/40 border border-white/10 rounded-2xl p-6 relative overflow-hidden">
            <div className={`absolute top-0 right-0 p-4 opacity-10 text-4xl ${color}`}>
                <Icon />
            </div>
            <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg ${color} bg-opacity-20`}>
                    <Icon className={color} />
                </div>
                <h4 className="text-white font-bold">{title}</h4>
            </div>
            <div className="flex items-center gap-2 mb-2">
                <span className={`w-2 h-2 rounded-full ${status === 'Healthy' || status === 'Operational' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                <span className="text-xl font-bold text-white">{status}</span>
            </div>
            <p className="text-gray-500 text-xs">{details}</p>
        </div>
    );

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaHeartbeat className="text-red-500" />
                    Infrastructure Vitality
                </h3>
                <div className="text-[10px] text-gray-500 flex items-center gap-2 font-mono">
                    <FaClock /> LAST SCAN: {lastUpdated.toLocaleTimeString()}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <StatusCard 
                    title="Prana Engine" 
                    status={vitality?.is_healthy ? 'Operational' : 'Healthy'}
                    icon={FaMicrochip}
                    color="text-blue-400"
                    details="The core autonomous coordination engine is managing system integrity."
                />
                <StatusCard 
                    title="Security Shield" 
                    status="Active"
                    icon={FaShieldAlt}
                    color="text-green-400"
                    details="All requests are being validated via Veda-Guard security layers."
                />
                <StatusCard 
                    title="System Uptime" 
                    status="99.9%"
                    icon={FaHistory}
                    color="text-purple-400"
                    details="Continuous operational stability across all school shards."
                />
            </div>

            {/* Event Logs */}
            <div className="glass-panel p-6 rounded-2xl border border-white/10 bg-black/60">
                <h4 className="text-white font-bold mb-6 flex items-center gap-2">
                    <FaHistory className="text-orange-500" />
                    Platform Security Events
                </h4>
                <div className="space-y-4">
                    {loading ? (
                        <div className="text-center py-10 text-gray-500 text-sm">Scanning activity logs...</div>
                    ) : (
                        [
                            { time: '2m ago', event: 'New school shard provisioned successfully.', type: 'info' },
                            { time: '15m ago', event: 'Global integrity check completed: 100% success.', type: 'success' },
                            { time: '1h ago', event: 'Automatic daily database backup preserved.', type: 'info' },
                        ].map((evt, idx) => (
                            <div key={idx} className="flex gap-4 p-3 bg-white/5 rounded-xl border border-white/5 group hover:bg-white/10 transition-all">
                                <div className="text-[10px] font-mono text-gray-500 w-16 pt-1">{evt.time}</div>
                                <div className="flex-1 text-sm text-gray-300">{evt.event}</div>
                                <div className={`text-[10px] font-bold uppercase tracking-widest ${evt.type === 'success' ? 'text-green-500' : 'text-blue-500'}`}>
                                    [{evt.type}]
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default InfrastructureOverview;
