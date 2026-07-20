import React from 'react';

/**
 * Error Boundary Component
 * Catches React errors and displays a graceful fallback UI
 * Prevents the entire app from crashing
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        // Log error to console (in production, send to error tracking service)
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        this.setState({
            error,
            errorInfo
        });
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
        // Optionally reload the page for a clean state
        // window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-black px-4">
                    <div className="max-w-md w-full glass-panel p-8 rounded-3xl border border-white/10 text-center">
                        <div className="mb-6">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">Something went wrong</h2>
                            <p className="text-gray-400 text-sm mb-6">
                                We encountered an unexpected error. Don't worry, your progress is safe.
                            </p>
                        </div>

                        <div className="space-y-3">
                            <button
                                onClick={this.handleReset}
                                className="w-full py-3 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-orange-500/20"
                            >
                                Try Recovery
                            </button>
                            <button
                                onClick={() => { window.location.reload(); }}
                                className="w-full py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl border border-white/10 transition-all"
                            >
                                Fresh Reload
                            </button>
                            <button
                                onClick={() => { window.location.hash = '#/dashboard'; this.handleReset(); }}
                                className="w-full py-3 text-gray-400 hover:text-white text-sm transition-all"
                            >
                                Go to Dashboard
                            </button>
                        </div>

                        {/* Error info and build version */}
                        <div className="mt-8 pt-6 border-t border-white/5">
                            <p className="text-[10px] text-gray-500 mb-2 uppercase tracking-widest">System Diagnostics</p>
                            <div className="flex justify-between text-[10px] text-gray-400">
                                <span>Build Version</span>
                                <span className="font-mono">v1.2.0-stable</span>
                            </div>

                            {(process.env.NODE_ENV === 'development' || true) && this.state.error && (
                                <details className="mt-4 text-left">
                                    <summary className="text-[10px] text-gray-500 cursor-pointer hover:text-gray-300 transition-colors uppercase tracking-widest">
                                        Stack Trace
                                    </summary>
                                    <pre className="mt-2 text-[10px] text-red-400/80 bg-black/40 p-3 rounded-lg overflow-auto max-h-32 border border-red-500/10 font-mono">
                                        {this.state.error.toString()}
                                        {this.state.errorInfo?.componentStack}
                                    </pre>
                                </details>
                            )}
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;

