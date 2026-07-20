import React from 'react';
import { FileText, Cpu, Layers, ListChecks } from 'lucide-react';

const PdfAnalysisCard = ({ analysis, alignment }) => {
    if (!analysis) return null;

    return (
        <div className="card border-l-4 border-l-blue-500 bg-gradient-to-br from-white to-blue-50/30 dark:from-slate-800 dark:to-blue-900/10">
            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-bold mb-6">
                <FileText size={20} />
                Documentation Insights (PDF)
            </div>

            <div className="grid md:grid-cols-2 gap-8">
                {/* Architecture Summary */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400">
                        <Layers size={14} />
                        Architecture Summary
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed italic border-l-2 border-slate-200 dark:border-slate-700 pl-4 py-1">
                        {analysis.architecture_description || "No specific architecture description detected."}
                    </p>

                    <div className="pt-2">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-bold ring-1 ring-blue-200 dark:ring-blue-800">
                            Alignment: {alignment?.toUpperCase() || "UNKNOWN"}
                        </div>
                    </div>
                </div>

                {/* Technical Stack */}
                <div className="space-y-6">
                    <div>
                        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                            <Cpu size={14} />
                            Technical Stack Detected
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {analysis.technical_stack?.length > 0 ? (
                                analysis.technical_stack.map((tech, i) => (
                                    <span key={i} className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs font-medium text-slate-600 dark:text-slate-300">
                                        {tech}
                                    </span>
                                ))
                            ) : (
                                <span className="text-xs text-slate-400 italic">No technical keywords detected.</span>
                            )}
                        </div>
                    </div>

                    <div>
                        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400 mb-3">
                            <ListChecks size={14} />
                            Documented Features
                        </div>
                        <ul className="space-y-1.5">
                            {analysis.documented_features?.length > 0 ? (
                                analysis.documented_features.slice(0, 5).map((feature, i) => (
                                    <li key={i} className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-2">
                                        <div className="w-1 h-1 rounded-full bg-blue-400" />
                                        {feature.length > 50 ? feature.slice(0, 50) + '...' : feature}
                                    </li>
                                ))
                            ) : (
                                <li className="text-xs text-slate-400 italic">No explicit features listed.</li>
                            )}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PdfAnalysisCard;
