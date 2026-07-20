import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const KarmaContext = createContext();

export const useKarma = () => {
    const context = useContext(KarmaContext);
    if (!context) {
        throw new Error('useKarma must be used within KarmaProvider');
    }
    return context;
};

// Karma Tracker is now integrated into backend - use same URL.
// In dev we use localhost, in production we default to the Gurukul backend on Render.
const KARMA_TRACKER_URL =
  import.meta.env.VITE_KARMA_TRACKER_URL ||
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? 'http://localhost:3000' : 'https://gurukul-up9j.onrender.com');

export const KarmaProvider = ({ children }) => {
    const { user } = useAuth();

    const [karma, setKarma] = useState(() => {
        const saved = localStorage.getItem('gurukul_karma');
        return saved ? parseInt(saved, 10) : 0;
    });

    // Ephemeral frontend-only notifications, driven by backend karma changes
    const [notifications, setNotifications] = useState([]);

    const addNotification = (amount, reason) => {
        if (!amount) return;
        const id = Date.now() + Math.random().toString(36).slice(2);
        const type = amount > 0 ? 'positive' : 'negative';

        setNotifications(prev => {
            // Avoid duplicate toasts with the same amount + reason
            const alreadyExists = prev.some(n => n.amount === amount && n.reason === reason);
            if (alreadyExists) return prev;
            return [...prev, { id, amount, reason, type }];
        });

        // Auto-remove after 4 seconds
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== id));
        }, 4000);
    };

    const removeNotification = (id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    };

    // Persist last known karma so users see something instantly on reload
    useEffect(() => {
        localStorage.setItem('gurukul_karma', karma.toString());
    }, [karma]);

    // Fetch karma from Karma Tracker
    const fetchKarmaFromTracker = React.useCallback(async () => {
        if (!user || !user.id) {
            console.log('[Karma] Cannot fetch karma - no user:', { user: !!user, userId: user?.id });
            return;
        }

        try {
            console.log('[Karma] Fetching karma for user:', user.id);
            const res = await fetch(`${KARMA_TRACKER_URL}/api/v1/karma/user/${user.id}`, {
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            if (!res.ok) {
                // Don't spam errors; just keep local value
                // 404 means user doesn't exist in Karma Tracker yet (not an error)
                if (res.status === 404) {
                    console.log('[Karma] User not found in Karma Tracker (will be created on first action)');
                } else {
                    console.warn('[Karma] Failed to fetch karma profile:', res.status, res.statusText);
                }
                return;
            }
            const data = await res.json();
            console.log('[Karma] Fetched karma data:', data);

            // Use DharmaPoints as the main visible karma metric
            const dharma = data?.balances?.DharmaPoints ?? 0;
            const nextKarma = Math.round(dharma);
            console.log('[Karma] Calculated karma:', { dharma, nextKarma });

            setKarma(prev => {
                const delta = nextKarma - prev;
                console.log('[Karma] Karma delta:', { prev, nextKarma, delta });

                // Check if this change came from PRANA (activity-based karma)
                let suppressNotification = false;
                try {
                    if (typeof window !== 'undefined' && window.localStorage) {
                        const silentFlag = localStorage.getItem('prana_silent_karma');
                        if (silentFlag === '1') {
                            suppressNotification = true;
                            localStorage.removeItem('prana_silent_karma');
                            console.log('[Karma] Suppressing notification for PRANA-driven karma change');
                        }
                    }
                } catch (e) {
                    // Ignore storage errors, fall back to normal behavior
                }

                if (delta !== 0 && !suppressNotification) {
                    const reason = delta > 0
                        ? 'Well done – your karma has increased.'
                        : 'A karmic penalty was applied. Reflect and realign.';
                    console.log('[Karma] Adding notification:', { delta, reason });
                    addNotification(delta, reason);
                } else if (delta === 0) {
                    console.log('[Karma] No karma change detected');
                }

                return nextKarma;
            });
        } catch (error) {
            console.warn('[Karma] Error fetching karma profile (non-blocking):', error);
        }
    }, [user?.id]);

    // Sync karma from Karma Tracker when user changes
    useEffect(() => {
        if (!user || !user.id) return;

        let cancelled = false;

        const fetchWithCancellation = async () => {
            if (cancelled) return;
            await fetchKarmaFromTracker();
        };

        // Initial fetch
        fetchWithCancellation();

        // Periodic refresh every 30 seconds
        const intervalId = setInterval(fetchWithCancellation, 30000);

        return () => {
            cancelled = true;
            clearInterval(intervalId);
        };
    }, [user?.id, fetchKarmaFromTracker]);

    return (
        <KarmaContext.Provider value={{ karma, notifications, removeNotification, refreshKarma: fetchKarmaFromTracker }}>
            {children}
        </KarmaContext.Provider>
    );
};
