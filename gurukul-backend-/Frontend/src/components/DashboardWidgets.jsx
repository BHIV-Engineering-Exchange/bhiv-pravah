import React from 'react';
import { FaClock, FaStar, FaBolt, FaTrophy, FaMedal, FaChartLine } from 'react-icons/fa';
import { useKarma } from '../contexts/KarmaContext';

export const StudyTimeWidget = ({ targetGoalSeconds, timeLeft, isActive, totalStudyTime }) => {

    const formatTime = (totalSeconds) => {
        const h = Math.floor(totalSeconds / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);
        const s = totalSeconds % 60;
        return `${h}h ${m}m ${s}s`;
    };

    // Progress Calculation
    let percentage = 0;
    let goalDisplay = "0h 0m 0s";

    if (isActive && targetGoalSeconds > 0) {
        const elapsed = targetGoalSeconds - timeLeft;
        percentage = Math.min(Math.floor((elapsed / targetGoalSeconds) * 100), 100);
        goalDisplay = formatTime(targetGoalSeconds);
    }

    return (
        <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/5 relative overflow-hidden group">
            <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
                <div className="p-1.5 sm:p-2 rounded-lg bg-blue-500/20 text-blue-400">
                    <FaClock className="text-sm sm:text-base" />
                </div>
                <h3 className="text-sm sm:text-base font-semibold text-gray-200">Today's Study Time</h3>
            </div>

            <div className="relative z-10">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold font-heading text-transparent bg-clip-text bg-gradient-to-r from-blue-200 to-white mb-2 tabular-nums notranslate">
                    {formatTime(totalStudyTime)}
                </div>
                <p className="text-xs text-blue-300/60 mb-3 sm:mb-4 notranslate">{percentage}% of daily goal ({goalDisplay})</p>

                {/* Progress Bar (Animation) */}
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-1000 ease-linear"
                        style={{ width: `${percentage}%` }}
                    ></div>
                </div>
            </div>

            {/* Decorative BG */}
            <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-blue-600/10 rounded-full blur-3xl group-hover:bg-blue-600/20 transition-all duration-500"></div>
        </div>
    );
};

export const KarmaWidget = () => {
    const { karma } = useKarma();

    // Determine karma level
    const getKarmaLevel = (points) => {
        if (points >= 400) return { label: 'Master', color: 'text-yellow-400', bg: 'bg-yellow-500/10' };
        if (points >= 300) return { label: 'Expert', color: 'text-orange-400', bg: 'bg-orange-500/10' };
        if (points >= 200) return { label: 'Scholar', color: 'text-purple-400', bg: 'bg-purple-500/10' };
        if (points >= 100) return { label: 'Learner', color: 'text-blue-400', bg: 'bg-blue-500/10' };
        return { label: 'Beginner', color: 'text-green-400', bg: 'bg-green-500/10' };
    };

    const level = getKarmaLevel(karma);

    return (
        <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/5 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 sm:gap-3">
                    <div className="p-1.5 sm:p-2 rounded-lg bg-purple-500/20 text-purple-400">
                        <FaStar className="text-sm sm:text-base" />
                    </div>
                    <h3 className="text-sm sm:text-base font-semibold text-gray-200">Karma</h3>
                </div>
                <span className={`text-[10px] sm:text-xs font-bold ${level.color} ${level.bg} px-1.5 sm:px-2 py-0.5 sm:py-1 rounded`}>{level.label}</span>
            </div>

            <div className="relative z-10 grid grid-cols-2 gap-3 sm:gap-4 mt-3 sm:mt-4">
                <div>
                    <div className="text-2xl sm:text-3xl md:text-4xl font-bold font-heading text-purple-200 notranslate">{karma}</div>
                    <p className="text-[10px] sm:text-xs text-purple-300/60 mt-1">Total Points</p>
                </div>
                <div className="text-xs space-y-2 text-gray-400 border-l border-white/10 pl-4">
                    <div className="flex justify-between">
                        <span>Positive</span>
                        <span className="text-green-400">+20</span>
                    </div>
                    <div className="flex justify-between">
                        <span>Negative</span>
                        <span className="text-red-400">-20</span>
                    </div>
                </div>
            </div>

            {/* Decorative BG */}
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-purple-600/10 rounded-full blur-3xl group-hover:bg-purple-600/20 transition-all duration-500"></div>
        </div>
    );
};

export const AchievementsWidget = () => (
    <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10 relative overflow-hidden row-span-2">
        <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
            <div className="p-1.5 sm:p-2 rounded-lg bg-yellow-500/20 text-yellow-400">
                <FaBolt className="text-sm sm:text-base" />
            </div>
            <h3 className="text-sm sm:text-base font-semibold text-gray-200">Achievements</h3>
        </div>

        <div className="space-y-3 sm:space-y-4">
            {[
                { icon: FaTrophy, label: "First Day Completed", color: "text-yellow-400" },
                { icon: FaChartLine, label: "Week Warrior", color: "text-orange-400" },
                { icon: FaMedal, label: "Goal Crusher", color: "text-green-400" },
                { icon: FaStar, label: "Streak Master", color: "text-blue-400" },
            ].map((item, i) => (
                <div key={i} className="flex items-center gap-4 group cursor-pointer">
                    <item.icon className={`text-lg ${item.color} opacity-80 group-hover:scale-110 transition-transform`} />
                    <span className="text-sm text-gray-300 group-hover:text-white transition-colors">{item.label}</span>
                </div>
            ))}
        </div>
    </div>
);

export const GoalWidget = ({ timeLeft, isActive, onStart, onStop }) => {
    const [isSetting, setIsSetting] = React.useState(false);

    // Split input states
    const [hrs, setHrs] = React.useState('00');
    const [mins, setMins] = React.useState('00');
    const [secs, setSecs] = React.useState('00');

    const handleStartClick = () => {
        const h = parseInt(hrs) || 0;
        const m = parseInt(mins) || 0;
        const s = parseInt(secs) || 0;
        const totalSeconds = (h * 3600) + (m * 60) + s;

        if (totalSeconds > 0 && onStart) {
            onStart(totalSeconds);
            setIsSetting(false);
        }
    };

    const handleStopClick = () => {
        if (onStop) onStop();
        setIsSetting(false);
        setHrs('00');
        setMins('00');
        setSecs('00');
    };

    const formatTime = (seconds) => {
        const totalSeconds = Number(seconds) || 0;
        const h = Math.floor(totalSeconds / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);
        const s = totalSeconds % 60;
        // Helper to pad with zeros
        const pad = (n) => n.toString().padStart(2, '0');
        return `${h}h ${pad(m)}m ${pad(s)}s`;
    };

    // Helper to handle 2-digit input
    const handleInput = (value, setter) => {
        // Allow only numbers, max 2 chars
        if (/^\d{0,2}$/.test(value)) {
            setter(value);
        }
    };

    return (
        <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10 relative overflow-hidden col-span-2 flex flex-col justify-center items-center text-center transition-all duration-300">
            <div className="mb-3 sm:mb-4">
                <FaTrophy className={`text-2xl sm:text-3xl text-accent mb-2 mx-auto transition-all ${isActive ? 'animate-pulse scale-110' : 'opacity-80'}`} />
                <h3 className="text-sm sm:text-base font-semibold text-gray-200">Daily Goal</h3>
            </div>

            {isSetting ? (
                <div className="flex flex-col items-center gap-4 animate-fade-in-up w-full">

                    {/* Time Inputs */}
                    <div className="flex items-center gap-1 sm:gap-2 text-xl sm:text-2xl md:text-3xl font-bold font-heading text-white">
                        <input
                            type="text"
                            value={hrs}
                            onChange={(e) => handleInput(e.target.value, setHrs)}
                            placeholder="00"
                            className="bg-transparent border-b-2 border-white/20 w-12 sm:w-14 md:w-16 text-center focus:outline-none focus:border-accent transition-colors placeholder-white/30 text-lg sm:text-xl md:text-2xl"
                        />
                        <span className="text-gray-400 -mt-2">:</span>
                        <input
                            type="text"
                            value={mins}
                            onChange={(e) => handleInput(e.target.value, setMins)}
                            placeholder="00"
                            className="bg-transparent border-b-2 border-white/20 w-12 sm:w-14 md:w-16 text-center focus:outline-none focus:border-accent transition-colors placeholder-white/30 text-lg sm:text-xl md:text-2xl"
                        />
                        <span className="text-gray-400 -mt-2">:</span>
                        <input
                            type="text"
                            value={secs}
                            onChange={(e) => handleInput(e.target.value, setSecs)}
                            placeholder="00"
                            className="bg-transparent border-b-2 border-white/20 w-12 sm:w-14 md:w-16 text-center focus:outline-none focus:border-accent transition-colors placeholder-white/30 text-lg sm:text-xl md:text-2xl"
                        />
                    </div>
                    <div className="flex justify-between w-full max-w-[200px] text-[9px] sm:text-[10px] uppercase tracking-wider text-gray-500 font-bold px-2">
                        <span>Hrs</span>
                        <span>Mins</span>
                        <span>Secs</span>
                    </div>

                    <div className="flex gap-2 w-full max-w-xs mt-2">
                        <button
                            onClick={() => setIsSetting(false)}
                            className="flex-1 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 text-sm font-medium transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleStartClick}
                            className="flex-1 px-4 py-2 rounded-lg bg-accent hover:bg-orange-500 text-white text-sm font-bold shadow-lg transition-all"
                        >
                            Start
                        </button>
                    </div>
                </div>
            ) : (
                <>
                    <div className="text-3xl sm:text-4xl md:text-5xl font-bold font-heading text-white mb-2 tabular-nums tracking-tight notranslate">
                        {formatTime(timeLeft)}
                    </div>

                    {isActive ? (
                        <button
                            onClick={handleStopClick}
                            className="mt-3 sm:mt-4 px-6 sm:px-8 py-2 sm:py-3 text-sm sm:text-base bg-red-500/80 hover:bg-red-600 text-white font-bold rounded-xl shadow-lg hover:shadow-red-500/20 transition-all transform hover:-translate-y-1"
                        >
                            Stop
                        </button>
                    ) : (
                        <button
                            onClick={() => {
                                setIsSetting(true);
                                setHrs('00');
                                setMins('00');
                                setSecs('00');
                            }}
                            className="mt-3 sm:mt-4 px-6 sm:px-8 py-2 sm:py-3 text-sm sm:text-base bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white font-bold rounded-xl shadow-lg hover:shadow-orange-500/20 transition-all transform hover:-translate-y-1"
                        >
                            Set New Goal
                        </button>
                    )}
                </>
            )}
        </div>
    );
};
