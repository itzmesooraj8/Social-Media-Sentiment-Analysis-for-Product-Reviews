
import React, { Component } from 'react';

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-gray-900 p-4">
                    <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-xl text-center border-t-4 border-red-500">
                        <h2 className="text-3xl font-bold mb-2 text-gray-800">System Maintenance</h2>
                        <p className="text-gray-500 mb-6 text-sm uppercase tracking-wide font-semibold">
                            Temporary Outage
                        </p>
                        <p className="text-gray-600 mb-8 leading-relaxed">
                            We encountered an unexpected issue while loading the application.
                            Our "Senior Developers" have been notified. Please try refreshing the page.
                        </p>

                        {/* Debug info for "Senior Devs" */}
                        {this.state.error && process.env.NODE_ENV === 'development' && (
                            <div className="bg-gray-100 p-4 rounded text-left text-xs font-mono mb-6 overflow-auto max-h-40">
                                {this.state.error.toString()}
                            </div>
                        )}

                        <div className="flex gap-4 justify-center">
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition shadow-lg font-medium"
                            >
                                Refresh Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
