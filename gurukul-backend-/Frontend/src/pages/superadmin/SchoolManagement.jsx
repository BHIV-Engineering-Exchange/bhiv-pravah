
import React, { useState, useEffect } from 'react';
import { FaUniversity, FaPlus, FaCheckCircle, FaTrash, FaExternalLinkAlt, FaDatabase } from 'react-icons/fa';
import { apiGet, apiPost, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const SchoolManagement = () => {
    const { alert, confirm } = useModal();
    const [schools, setSchools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        subdomain_slug: '',
        database_url: ''
    });

    useEffect(() => {
        fetchSchools();
    }, []);

    const fetchSchools = async () => {
        setLoading(true);
        try {
            const data = await apiGet('/api/v1/ems/tenants');
            setSchools(data);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch schools' });
            // await alert(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const handleProvision = async (e) => {
        e.preventDefault();
        try {
            await apiPost('/api/v1/ems/provision-tenant', formData);
            await alert('School provisioned successfully! The new database and schema have been initialized.', 'Success');
            setIsFormOpen(false);
            setFormData({ name: '', subdomain_slug: '', database_url: '' });
            fetchSchools();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'provision school' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    return (
        <div className="space-y-6">
            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <FaUniversity className="text-orange-500" />
                            Registered Schools
                        </h3>
                        <p className="text-gray-400 text-xs mt-1">Manage and provision individual institutions on the platform.</p>
                    </div>
                    <button 
                        onClick={() => setIsFormOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg text-white font-bold text-sm transition-all"
                    >
                        <FaPlus /> Provision New School
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {loading ? (
                        <div className="col-span-full py-20 flex flex-col items-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mb-2"></div>
                            <span className="text-gray-500 text-sm">Loading schools...</span>
                        </div>
                    ) : schools.length === 0 ? (
                        <div className="col-span-full py-12 text-center text-gray-400 bg-white/5 rounded-xl border border-dashed border-white/10">
                            No schools registered yet.
                        </div>
                    ) : (
                        schools.map(school => (
                            <div key={school.id} className="bg-black/40 border border-white/10 rounded-xl p-5 hover:border-orange-500/50 transition-all group">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400">
                                        <FaUniversity />
                                    </div>
                                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-500/20 text-green-400 uppercase border border-green-500/30">
                                        Active
                                    </span>
                                </div>
                                <h4 className="text-white font-bold mb-1 truncate">{school.name}</h4>
                                <p className="text-gray-500 text-xs mb-4 font-mono">{school.id}</p>
                                
                                <div className="space-y-2 mb-4">
                                    <div className="flex items-center gap-2 text-xs text-gray-400">
                                        <FaDatabase className="opacity-50" />
                                        <span className="truncate">{school.subdomain_slug || 'No slug'}</span>
                                    </div>
                                </div>

                                <div className="flex gap-2">
                                    <button className="flex-1 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-bold transition-all border border-white/10">
                                        Manage
                                    </button>
                                    <button className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-all border border-red-500/20">
                                        <FaTrash size={12} />
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Provision Modal */}
            {isFormOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-gray-900 border border-white/10 rounded-2xl w-full max-w-md p-6 animate-fade-in-up">
                        <h3 className="text-xl font-bold text-white mb-4">Provision New School</h3>
                        <form onSubmit={handleProvision} className="space-y-4">
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">School Name</label>
                                <input 
                                    type="text" required
                                    value={formData.name}
                                    onChange={e => setFormData({...formData, name: e.target.value})}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-orange-500"
                                    placeholder="e.g. St. Xaviers Academy"
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Subdomain Slug</label>
                                <input 
                                    type="text" required
                                    value={formData.subdomain_slug}
                                    onChange={e => setFormData({...formData, subdomain_slug: e.target.value})}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-orange-500"
                                    placeholder="e.g. xaviers-north"
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">Custom Database URL (Optional)</label>
                                <input 
                                    type="text"
                                    value={formData.database_url}
                                    onChange={e => setFormData({...formData, database_url: e.target.value})}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-orange-500"
                                    placeholder="postgresql://user:pass@host/db"
                                />
                                <p className="text-[10px] text-gray-500 mt-1">Leave empty to use the platform's central PostgreSQL server.</p>
                            </div>
                            <div className="flex gap-3 pt-4">
                                <button 
                                    type="button" 
                                    onClick={() => setIsFormOpen(false)}
                                    className="flex-1 py-2 rounded-lg bg-gray-800 text-white text-sm font-bold"
                                >
                                    Cancel
                                </button>
                                <button 
                                    type="submit" 
                                    className="flex-1 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white text-sm font-bold shadow-lg shadow-orange-600/20"
                                >
                                    Create School
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SchoolManagement;
