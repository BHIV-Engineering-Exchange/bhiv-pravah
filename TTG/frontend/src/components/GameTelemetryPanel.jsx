import { useState, useEffect } from 'react';
import socket from '../socket/socket';
import { speak } from '../utils/tts';

export default function GameTelemetryPanel() {
  const [telemetry, setTelemetry] = useState({
    fps: 0,
    score: 0,
    game_over: false,
    lives: 0,
    duration: 0
  });
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    socket.on('telemetry', (data) => {
      setTelemetry(prev => ({
        ...prev,
        ...data
      }));
      if (data.game_over) {
        setIsPlaying(false);
      }
    });

    socket.on('game:started', () => {
      setIsPlaying(true);
      speak('Game started');
      setTelemetry({
        fps: 0,
        score: 0,
        game_over: false,
        lives: 0,
        duration: 0
      });
    });

    socket.on('game:ended', (data) => {
      setIsPlaying(false);
      speak('Game over');
      setTelemetry(prev => ({
        ...prev,
        game_over: true,
        ...data
      }));
    });

    return () => {
      socket.off('telemetry');
      socket.off('game:started');
      socket.off('game:ended');
    };
  }, []);

  return (
    <div className="relative backdrop-blur-2xl border rounded-3xl overflow-hidden shadow-[0_18px_45px_rgba(15,23,42,0.6)] transition-all duration-500 bg-gradient-to-br from-slate-50/90 via-white/90 to-sky-50/90 dark:from-slate-950/90 dark:via-slate-900/80 dark:to-slate-950/95 border-slate-200/80 dark:border-slate-800/80 p-6 flex flex-col hover:shadow-[0_20px_50px_rgba(139,92,246,0.3)] hover:border-violet-400/50 dark:hover:border-violet-500/50">
      {/* Animated background blobs */}
      <div className="pointer-events-none absolute inset-0 opacity-40 mix-blend-screen">
        <div className="absolute -top-32 -right-16 h-56 w-56 rounded-full bg-violet-500/30 blur-3xl animate-pulse" />
        <div className={`absolute -bottom-40 -left-10 h-60 w-60 rounded-full blur-3xl transition-all duration-1000 ${
          isPlaying ? 'bg-green-500/40 animate-pulse' : 'bg-indigo-500/25'
        }`} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-40 w-40 rounded-full bg-pink-500/20 blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="relative flex-1 flex flex-col">
        {/* Header */}
        <div className="mb-6 pb-4 border-b border-slate-200/60 dark:border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
           
              <h2 className="text-lg font-bold bg-gradient-to-r from-violet-400 via-purple-400 to-pink-400 bg-clip-text text-transparent tracking-tight">
                Game Telemetry
              </h2>
            </div>
            <span className={`px-4 py-1.5 text-xs font-bold rounded-full border-2 backdrop-blur-sm flex items-center gap-2 transition-all duration-300 ${
              isPlaying 
                ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white border-green-400 shadow-lg shadow-green-500/50 animate-pulse' 
                : telemetry.game_over
                ? 'bg-gradient-to-r from-red-500 to-rose-500 text-white border-red-400 shadow-lg shadow-red-500/50'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-600'
            }`}>
              <span className={`inline-flex h-2 w-2 rounded-full ${
                isPlaying ? 'bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)]' : 'bg-slate-400'
              }`} />
              {isPlaying ? 'LIVE' : telemetry.game_over ? 'ENDED' : 'IDLE'}
            </span>
          </div>
        </div>

        {/* Score Display - Hero Section */}
        <div className="mb-4 sm:mb-6 p-4 sm:p-8 rounded-2xl bg-gradient-to-br from-indigo-500/20 via-violet-500/20 to-purple-500/20 border-2 border-indigo-400/60 dark:border-indigo-500/60 backdrop-blur-sm shadow-[0_8px_32px_rgba(139,92,246,0.2)] relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300">
          <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="relative text-center">
            <div className="text-[10px] sm:text-xs uppercase tracking-[0.2em] text-violet-600 dark:text-violet-400 mb-2 sm:mb-4 font-bold flex items-center justify-center gap-2">
              <span className="inline-block w-6 sm:w-12 h-[2px] bg-gradient-to-r from-transparent via-violet-500 to-transparent" />
              SCORE
              <span className="inline-block w-6 sm:w-12 h-[2px] bg-gradient-to-r from-transparent via-violet-500 to-transparent" />
            </div>
            <div className="text-4xl sm:text-7xl font-black bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent drop-shadow-[0_0_20px_rgba(139,92,246,0.5)] animate-pulse" style={{ animationDuration: '2s' }}>
              {telemetry.score.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-4 sm:mb-6">
          {/* FPS */}
          <div className="group p-3 sm:p-5 rounded-xl sm:rounded-2xl bg-gradient-to-br from-white/80 to-white/60 dark:from-slate-900/80 dark:to-slate-950/60 border-2 border-slate-200/70 dark:border-slate-700/70 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-green-400/50 dark:hover:border-green-500/50 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="relative">
              <div className="text-[9px] sm:text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-1 sm:mb-3 font-bold">FPS</div>
              <div className={`text-2xl sm:text-4xl font-black transition-all duration-300 ${
                telemetry.fps >= 50 ? 'text-green-500 drop-shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 
                telemetry.fps >= 30 ? 'text-yellow-500 drop-shadow-[0_0_8px_rgba(234,179,8,0.5)]' : 
                'text-red-500 drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]'
              }`}>
                {telemetry.fps}
              </div>
            </div>
          </div>

          {/* Lives */}
          <div className="group p-3 sm:p-5 rounded-xl sm:rounded-2xl bg-gradient-to-br from-white/80 to-white/60 dark:from-slate-900/80 dark:to-slate-950/60 border-2 border-slate-200/70 dark:border-slate-700/70 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-red-400/50 dark:hover:border-red-500/50 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-rose-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="absolute top-1 right-1 sm:top-2 sm:right-2 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-red-500 text-white text-xs sm:text-base font-black flex items-center justify-center shadow-lg z-10">
              {telemetry.lives}
            </div>
            <div className="relative">
              <div className="text-[9px] sm:text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-1 sm:mb-3 font-bold">Lives</div>
              <div className="text-xl sm:text-3xl font-bold flex gap-0.5 sm:gap-1">
                {Array.from({ length: Math.max(telemetry.lives, 3) }).map((_, i) => (
                  <span key={i} className={`transition-all duration-300 text-base sm:text-2xl ${
                    i < telemetry.lives 
                      ? 'opacity-100 scale-100 drop-shadow-[0_0_8px_rgba(239,68,68,0.6)]' 
                      : 'opacity-20 scale-75 grayscale'
                  }`}>
                    ❤️
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Duration */}
          <div className="group p-3 sm:p-5 rounded-xl sm:rounded-2xl bg-gradient-to-br from-white/80 to-white/60 dark:from-slate-900/80 dark:to-slate-950/60 border-2 border-slate-200/70 dark:border-slate-700/70 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-cyan-400/50 dark:hover:border-cyan-500/50 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="relative">
              <div className="text-[9px] sm:text-xs uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-1 sm:mb-3 font-bold">Time</div>
              <div className="text-2xl sm:text-4xl font-black text-cyan-500 drop-shadow-[0_0_8px_rgba(6,182,212,0.5)]">
                {Math.floor(telemetry.duration)}s
              </div>
            </div>
          </div>
        </div>

        {/* Game Over Message */}
        {telemetry.game_over && (
          <div className="p-4 sm:p-6 rounded-2xl bg-gradient-to-br from-red-500/20 via-rose-500/20 to-red-600/20 border-2 border-red-500/60 backdrop-blur-sm shadow-[0_8px_32px_rgba(239,68,68,0.3)] animate-pulse relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 via-transparent to-rose-500/10 animate-pulse" style={{ animationDuration: '3s' }} />
            <div className="relative text-center">
              <div className="text-2xl sm:text-4xl font-black text-red-500 mb-2 sm:mb-4 drop-shadow-[0_0_12px_rgba(239,68,68,0.6)] flex items-center justify-center gap-2 sm:gap-3">
                <span className="animate-bounce text-xl sm:text-3xl">💀</span>
                GAME OVER
                <span className="animate-bounce text-xl sm:text-3xl" style={{ animationDelay: '0.2s' }}>💀</span>
              </div>
              <div className="text-sm sm:text-base text-slate-600 dark:text-slate-300 font-medium">
                Final Score: <span className="text-xl sm:text-2xl font-black bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">{telemetry.score.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}

        {/* Idle State Message */}
        {!isPlaying && !telemetry.game_over && (
          <div className="flex-1 flex items-center justify-center p-4 sm:p-8">
            <div className="text-center">
              <div className="text-4xl sm:text-6xl mb-2 sm:mb-4 animate-bounce">🎮</div>
              <h3 className="text-base sm:text-xl font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent mb-1 sm:mb-2">Waiting for Game</h3>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">Start a game to see live telemetry</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
