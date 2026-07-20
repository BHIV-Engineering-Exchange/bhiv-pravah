import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Award, UserCheck, ShieldCheck, Activity, Calendar, AlertTriangle } from 'lucide-react';
import LoadingState from '../components/LoadingState';

const Analytics = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [buildersData, setBuildersData] = useState([]);
    const [productsData, setProductsData] = useState([]);
    const [trendsData, setTrendsData] = useState([]);

    const getBackendUrl = () => {
        let backendUrl = process.env.REACT_APP_API_BASE
            || process.env.REACT_APP_BACKEND_URL
            || 'http://localhost:8000/api/v1';
        backendUrl = backendUrl.replace(/\/+$/, '');
        if (!backendUrl.endsWith('/api/v1')) {
            backendUrl = `${backendUrl}/api/v1`;
        }
        return backendUrl;
    };

    const getHeaders = () => {
        const token = localStorage.getItem('parikshak_token');
        return {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
    };

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            const baseUrl = getBackendUrl();
            const headers = getHeaders();

            // Fetch builder-quality
            const builderRes = await fetch(`${baseUrl}/dashboard/builder-quality`, { headers });
            if (!builderRes.ok) throw new Error(`Builder endpoint returned status ${builderRes.status}`);
            const builderJson = await builderRes.json();
            setBuildersData(builderJson.builders || []);

            // Fetch product-readiness
            const productRes = await fetch(`${baseUrl}/dashboard/product-readiness`, { headers });
            if (!productRes.ok) throw new Error(`Product endpoint returned status ${productRes.status}`);
            const productJson = await productRes.json();
            setProductsData(productJson.products || []);

            // Fetch engineering-trends
            const trendRes = await fetch(`${baseUrl}/dashboard/engineering-trends?days=30`, { headers });
            if (!trendRes.ok) throw new Error(`Trends endpoint returned status ${trendRes.status}`);
            const trendJson = await trendRes.json();
            setTrendsData(trendJson.trends || []);

            setError(null);
        } catch (err) {
            console.error('Failed to load analytics metrics:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, []);

    if (loading) return <LoadingState message="Loading analytical governance index..." />;

    if (error) {
        return (
            <div className="max-w-4xl mx-auto p-6 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-center space-y-4">
                <AlertTriangle className="mx-auto text-rose-500" size={48} />
                <h3 className="text-lg font-black text-rose-400">Failed to Retrieve Analytics</h3>
                <p className="text-xs text-slate-400">{error}</p>
                <button 
                    onClick={fetchAnalytics}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all"
                >
                    Retry Connection
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto space-y-8 fade-in">
            {/* Header */}
            <header className="border-b border-[#1a243a] pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-2">
                        <BarChart3 size={28} className="text-blue-500" /> Analytics Portal
                    </h1>
                    <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">BHIV Governance & Quality Trends</p>
                </div>
                <button 
                    onClick={fetchAnalytics}
                    className="px-4 py-2 bg-[#131f37] hover:bg-[#1e2e4f] border border-[#1a243a] rounded-xl text-xs font-bold transition-all"
                >
                    Refresh Metrics
                </button>
            </header>

            {/* Product Readiness List */}
            <section className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-4">
                <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                    <Award size={16} className="text-indigo-500" />
                    Ecosystem Product Readiness Status
                </h3>
                {productsData.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {productsData.map((p) => {
                            const isReady = p.certification_status === 'READY';
                            return (
                                <div key={p.product_id} className="p-4 bg-[#131f37] rounded-xl border border-[#1a243a] flex flex-col justify-between space-y-4">
                                    <div className="space-y-1">
                                        <h4 className="font-extrabold text-sm text-white">{p.product_name}</h4>
                                        <div className="text-[10px] text-slate-500 font-mono">ID: {p.product_id}</div>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className={`text-[9px] font-black uppercase px-2.5 py-0.5 rounded border ${
                                            isReady 
                                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                        }`}>
                                            {p.certification_status}
                                        </span>
                                        <div className="text-right">
                                            <div className="text-[10px] font-black text-slate-500">Readiness Score</div>
                                            <div className="text-xs font-black text-white">{p.readiness_score}%</div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="text-center py-8 text-xs text-slate-500">No ecosystem products registered.</div>
                )}
            </section>

            {/* Split layout: Builders and Daily Trends */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                {/* Builders/Candidates quality */}
                <section className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-4">
                    <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                        <UserCheck size={16} className="text-blue-500" />
                        Candidate / Builder Quality Metrics
                    </h3>
                    {buildersData.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs">
                                <thead>
                                    <tr className="border-b border-[#1a243a] text-slate-500 font-black uppercase text-[10px]">
                                        <th className="pb-3">Builder</th>
                                        <th className="pb-3 text-center">Reviews</th>
                                        <th className="pb-3 text-center">Pass Rate</th>
                                        <th className="pb-3 text-right">Avg Score</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#1a243a]/50 font-bold">
                                    {buildersData.map((b, idx) => (
                                        <tr key={idx} className="hover:bg-[#131f37]/35 transition-all">
                                            <td className="py-3 text-white">{b.builder_name}</td>
                                            <td className="py-3 text-center text-slate-400">{b.total_reviews}</td>
                                            <td className="py-3 text-center text-emerald-400">{b.pass_rate_percent}%</td>
                                            <td className="py-3 text-right text-indigo-400">{b.average_score}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-xs text-slate-500">No builder metrics log records.</div>
                    )}
                </section>

                {/* Daily review trends list */}
                <section className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-4">
                    <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                        <TrendingUp size={16} className="text-indigo-500" />
                        Daily Engineering Trends (30 Days)
                    </h3>
                    {trendsData.length > 0 ? (
                        <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                            {trendsData.map((t, idx) => (
                                <div key={idx} className="p-3 bg-[#131f37] rounded-xl border border-[#1a243a] flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-2">
                                        <Calendar size={14} className="text-slate-500" />
                                        <span className="font-black text-white">{t.date}</span>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase font-black mr-2">Reviews</span>
                                            <span className="font-black text-slate-300">{t.reviews_count}</span>
                                        </div>
                                        <div>
                                            <span className="text-[10px] text-slate-500 uppercase font-black mr-2">Avg Score</span>
                                            <span className="font-black text-blue-400">{t.average_score}%</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-xs text-slate-500">No review trend data recorded.</div>
                    )}
                </section>

            </div>
        </div>
    );
};

export default Analytics;
