import React from 'react';
import { Shield, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const RegistryValidationCard = ({ validation }) => {
    if (!validation) return null;

    const getStatusIcon = (passed) => {
        if (passed) return <CheckCircle size={16} className="text-emerald-500" />;
        return <XCircle size={16} className="text-red-500" />;
    };

    const getStatusColor = (passed) => {
        return passed ? 'border-emerald-200 bg-emerald-50 dark:bg-emerald-900/20' : 'border-red-200 bg-red-50 dark:bg-red-900/20';
    };

    return (
        <div className={`card ${getStatusColor(validation.validation_passed)} border-2`}>
            <div className="flex items-center gap-2 mb-4">
                <Shield size={20} className="text-blue-600" />
                <span className="font-bold text-slate-800 dark:text-slate-200">Blueprint Registry Validation</span>
                {getStatusIcon(validation.validation_passed)}
            </div>

            <div className="grid md:grid-cols-3 gap-4 text-sm">
                <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg">
                    <span className="text-slate-600 dark:text-slate-400">Module ID</span>
                    <div className="flex items-center gap-2">
                        <span className="font-semibold">{validation.module_id || 'N/A'}</span>
                        {getStatusIcon(validation.module_id_valid)}
                    </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg">
                    <span className="text-slate-600 dark:text-slate-400">Lifecycle Stage</span>
                    <div className="flex items-center gap-2">
                        <span className="font-semibold">Active</span>
                        {getStatusIcon(validation.lifecycle_stage_valid)}
                    </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-lg">
                    <span className="text-slate-600 dark:text-slate-400">Schema Version</span>
                    <div className="flex items-center gap-2">
                        <span className="font-semibold">{validation.schema_version || '1.0'}</span>
                        {getStatusIcon(validation.schema_version_valid)}
                    </div>
                </div>
            </div>

            {!validation.validation_passed && (
                <div className="mt-4 p-3 bg-red-100 dark:bg-red-900/30 rounded-lg border border-red-200 dark:border-red-800">
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-semibold mb-2">
                        <AlertTriangle size={16} />
                        Registry Validation Failed
                    </div>
                    <p className="text-sm text-red-700 dark:text-red-300">
                        Task rejected due to structural discipline violations. Please ensure your task belongs to a valid Blueprint Registry module and meets schema requirements.
                    </p>
                </div>
            )}
        </div>
    );
};

export default RegistryValidationCard;