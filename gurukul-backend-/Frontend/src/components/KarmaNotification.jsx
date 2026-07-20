import React from 'react';
import { useKarma } from '../contexts/KarmaContext';
import { FaStar, FaTimes } from 'react-icons/fa';

const KarmaNotification = () => {
    const { notifications, removeNotification } = useKarma();

    return (
        <div className="fixed top-20 sm:top-24 right-2 sm:right-6 z-[10000] flex flex-col gap-2 sm:gap-3 max-w-[calc(100vw-1rem)]">
            {notifications.map((notification) => (
                <div
                    key={notification.id}
                    className={`
                        flex items-center gap-2 sm:gap-3 px-3 sm:px-5 py-2 sm:py-3 rounded-xl shadow-2xl border-2
                        backdrop-blur-md animate-slide-in-right min-w-[200px] sm:min-w-[280px] max-w-[calc(100vw-1rem)]
                        ${notification.type === 'positive'
                            ? 'bg-green-600/90 border-green-400 text-white'
                            : 'bg-red-600/90 border-red-400 text-white'
                        }
                    `}
                >
                    <FaStar className="text-lg sm:text-2xl flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                        <div className="font-bold text-sm sm:text-lg">
                            {notification.amount > 0 ? '+' : ''}{notification.amount} Karma
                        </div>
                        <div className="text-xs sm:text-sm opacity-90 truncate">{notification.reason}</div>
                    </div>
                    <button
                        onClick={() => removeNotification(notification.id)}
                        className="text-white/70 hover:text-white transition-colors"
                    >
                        <FaTimes />
                    </button>
                </div>
            ))}
        </div>
    );
};

export default KarmaNotification;
