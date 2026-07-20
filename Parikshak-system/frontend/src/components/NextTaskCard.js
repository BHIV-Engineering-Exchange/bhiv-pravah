import React from 'react';
import { Target, List, Play, Info } from 'lucide-react';
import Button from './ui/Button';
import TtsButton from './TtsButton';

const NextTaskCard = ({ task }) => {
    const getDifficultyColor = (diff) => {
        switch (diff?.toLowerCase()) {
            case 'beginner': return 'text-emerald-500 bg-emerald-500/10';
            case 'intermediate': return 'text-blue-500 bg-blue-500/10';
            case 'advanced': return 'text-amber-500 bg-amber-500/10';
            case 'expert': return 'text-red-500 bg-red-500/10';
            default: return 'text-slate-500 bg-slate-500/10';
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-8 fade-in">
            <div className="text-center space-y-2">
                <h2 className="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tight">Your Next Mission</h2>
                <p className="text-slate-500">The system has analyzed your progress and assigned a new task.</p>
            </div>

            <div className="card overflow-hidden !p-0">
                <div className="p-8 space-y-6">
                    <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm font-bold text-blue-600 dark:text-blue-400 uppercase tracking-widest">
                                <Target size={16} />
                                Current Assignment
                            </div>
                            <h3 className="text-2xl font-bold">{task?.title || 'No task title'}</h3>
                        </div>
                        <div className="flex items-center gap-2">
                            <TtsButton
                                text={task?.title || ''}
                                lang="en"
                                tone="formal"
                                showControls={true}
                            />
                            <span className={`px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-wider ${getDifficultyColor(task?.difficulty)}`}>
                                {task?.difficulty || 'General'}
                            </span>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="p-6 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300 font-bold">
                                    <List size={18} className="text-blue-500" />
                                    Project Objective
                                </div>
                                <TtsButton
                                    text={task?.objective || ''}
                                    lang="en"
                                    tone="educational"
                                    showControls={false}
                                />
                            </div>
                            <p className="text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                                {task?.objective || 'No objective available for this task.'}
                            </p>
                        </div>

                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shadow-sm">
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Focus Area</div>
                                <div className="text-sm font-bold text-blue-600 dark:text-blue-400">{task?.focus_area || 'General Review'}</div>
                            </div>
                            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shadow-sm">
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Assignment Type</div>
                                <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 uppercase">{task?.task_type || 'Training'}</div>
                            </div>
                        </div>

                        <div className="p-4 bg-amber-500/5 border border-amber-500/10 rounded-2xl">
                            <div className="flex items-start gap-3">
                                <Info size={16} className="text-amber-500 mt-0.5" />
                                <div className="flex-1">
                                    <div className="flex items-center justify-between">
                                        <div className="text-xs font-bold text-amber-600 uppercase tracking-tight">System Rationale</div>
                                        <TtsButton text={task?.reason || ''} lang="en" tone="calm" />
                                    </div>
                                    <p className="text-sm text-slate-500 dark:text-slate-400 italic mt-1 leading-snug">
                                        {task?.reason || 'Task optimized for your current skill progression levels.'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {task?.dharma && (
                            <div className="p-4 bg-purple-500/5 border border-purple-500/10 rounded-2xl">
                                <div className="flex items-start gap-3">
                                    <span className="text-purple-500 mt-0.5 text-lg leading-none">&#9670;</span>
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase tracking-tight">Dharma</div>
                                            <TtsButton text={task.dharma} lang="en" tone="educational" />
                                        </div>
                                        <p className="text-sm text-purple-700 dark:text-purple-300 italic leading-snug font-medium">
                                            {task.dharma}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {task?.dharma && (
                            <div className="p-4 bg-purple-500/5 border border-purple-500/10 rounded-2xl">
                                <div className="flex items-start gap-3">
                                    <span className="text-purple-500 mt-0.5 text-base">&#9670;</span>
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between">
                                            <div className="text-xs font-bold text-purple-600 dark:text-purple-400 uppercase tracking-tight">Dharma</div>
                                            <TtsButton text={task.dharma} lang="en" tone="educational" />
                                        </div>
                                        <p className="text-sm text-purple-700 dark:text-purple-300 italic mt-1 leading-snug font-medium">
                                            {task.dharma}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="bg-slate-50/80 dark:bg-slate-800/80 p-6 flex justify-center border-t border-slate-100 dark:border-slate-800">
                    <Button size="lg" className="w-full md:w-auto px-12 group">
                        <Play size={20} fill="currentColor" className="group-hover:scale-110 transition-transform" />
                        Start Task
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default NextTaskCard;
