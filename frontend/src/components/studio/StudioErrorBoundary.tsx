/** StudioErrorBoundary — React error boundary with fallback UI */
import React from 'react';

interface Props {
  children: React.ReactNode;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class StudioErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('StudioErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="flex flex-col items-center justify-center h-full p-6 gap-4"
          style={{ background: 'var(--t-bg)' }}
        >
          {/* Error icon */}
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(239, 68, 68, 0.12)' }}
          >
            <svg
              className="w-7 h-7"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
              style={{ color: 'var(--t-error)' }}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>

          {/* Message */}
          <div className="text-center max-w-sm">
            <h3 className="text-sm font-medium mb-1" style={{ color: 'var(--t-text)' }}>
              Something went wrong
            </h3>
            <p className="text-xs mb-3" style={{ color: 'var(--t-muted)' }}>
              {this.props.fallbackMessage || 'An unexpected error occurred in the Studio component.'}
            </p>

            {/* Error details */}
            {this.state.error && (
              <div
                className="text-left text-xs p-3 rounded mb-3 max-h-24 overflow-auto"
                style={{
                  background: 'var(--t-surface)',
                  color: 'var(--t-error)',
                  border: '1px solid var(--t-border)',
                  fontFamily: 'var(--t-font-mono)',
                }}
              >
                {this.state.error.message}
              </div>
            )}
          </div>

          {/* Reset button */}
          <button
            onClick={this.handleReset}
            className="px-4 py-2 rounded-lg text-xs font-medium transition-colors"
            style={{ background: 'var(--t-primary)', color: '#fff' }}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default StudioErrorBoundary;
