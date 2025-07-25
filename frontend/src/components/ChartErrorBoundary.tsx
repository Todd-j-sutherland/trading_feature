import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onRetry?: () => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  retryCount: number;
}

class ChartErrorBoundary extends Component<Props, State> {
  private retryTimer?: NodeJS.Timeout;

  constructor(props: Props) {
    super(props);
    this.state = { 
      hasError: false, 
      retryCount: 0 
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Chart Error Boundary Caught:', error);
    console.error('Error Info:', errorInfo.componentStack);
    
    // Store error info for debugging
    this.setState({ errorInfo });

    // Auto-retry up to 3 times with exponential backoff
    if (this.state.retryCount < 3) {
      const delay = Math.pow(2, this.state.retryCount) * 1000; // 1s, 2s, 4s
      this.retryTimer = setTimeout(() => {
        this.handleRetry();
      }, delay);
    }
  }

  componentWillUnmount() {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }
  }

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      retryCount: prevState.retryCount + 1
    }));

    // Call external retry handler if provided
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isNetworkError = this.state.error?.message.includes('fetch') || 
                           this.state.error?.message.includes('network');
      const isDataError = this.state.error?.message.includes('data') ||
                         this.state.error?.message.includes('chart');

      return (
        <div className="flex flex-col items-center justify-center h-96 bg-gray-900 rounded-lg border border-red-500/50 p-6">
          <div className="text-red-400 text-2xl mb-4">
            {isNetworkError ? '🌐' : isDataError ? '📊' : '⚠️'} Chart Error
          </div>
          
          <div className="text-gray-300 text-center max-w-md mb-4">
            <p className="mb-2 font-medium">
              {isNetworkError && 'Network connection issue detected'}
              {isDataError && 'Chart data processing error'}
              {!isNetworkError && !isDataError && 'The trading chart encountered an error'}
            </p>
            
            <p className="text-sm text-gray-400 mb-4">
              {isNetworkError && 'Please check your internet connection and try again.'}
              {isDataError && 'The chart data may be corrupted or incomplete.'}
              {!isNetworkError && !isDataError && (this.state.error?.message || 'Unknown error occurred')}
            </p>

            {this.state.retryCount > 0 && (
              <p className="text-xs text-yellow-400 mb-2">
                Retry attempt {this.state.retryCount}/3
              </p>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={this.handleRetry}
              disabled={this.state.retryCount >= 3}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded transition-colors"
            >
              {this.state.retryCount >= 3 ? 'Max Retries Reached' : 'Retry Chart'}
            </button>

            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
            >
              Reload Page
            </button>
          </div>

          {this.props.showDetails && this.state.error && (
            <details className="mt-4 w-full max-w-lg">
              <summary className="text-sm text-gray-400 cursor-pointer hover:text-gray-300">
                Show Error Details
              </summary>
              <div className="mt-2 p-3 bg-gray-800 rounded text-xs text-red-300 overflow-auto max-h-32">
                <div className="font-mono">
                  <div className="mb-2">
                    <strong>Error:</strong> {this.state.error.message}
                  </div>
                  {this.state.error.stack && (
                    <div>
                      <strong>Stack:</strong>
                      <pre className="whitespace-pre-wrap">{this.state.error.stack}</pre>
                    </div>
                  )}
                </div>
              </div>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ChartErrorBoundary;
