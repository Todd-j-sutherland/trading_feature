import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';

interface ErrorInfo {
  id: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  timestamp: Date;
  details?: string;
  retryAction?: () => void;
}

interface ErrorContextType {
  errors: ErrorInfo[];
  addError: (message: string, type?: ErrorInfo['type'], details?: string, retryAction?: () => void) => string;
  removeError: (id: string) => void;
  clearAllErrors: () => void;
  networkStatus: {
    isOnline: boolean;
    lastOfflineTime?: Date;
  };
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

interface ErrorProviderProps {
  children: ReactNode;
  maxErrors?: number;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ 
  children, 
  maxErrors = 5 
}) => {
  const [errors, setErrors] = useState<ErrorInfo[]>([]);
  const [networkStatus, setNetworkStatus] = useState({
    isOnline: navigator.onLine,
    lastOfflineTime: undefined as Date | undefined,
  });

  // Monitor network status
  React.useEffect(() => {
    const handleOnline = () => {
      setNetworkStatus(prev => ({ ...prev, isOnline: true }));
    };

    const handleOffline = () => {
      setNetworkStatus({
        isOnline: false,
        lastOfflineTime: new Date(),
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const addError = useCallback((
    message: string, 
    type: ErrorInfo['type'] = 'error',
    details?: string,
    retryAction?: () => void
  ): string => {
    const id = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const newError: ErrorInfo = {
      id,
      message,
      type,
      timestamp: new Date(),
      details,
      retryAction,
    };

    setErrors(prev => {
      const updated = [newError, ...prev];
      // Keep only the latest maxErrors
      return updated.slice(0, maxErrors);
    });

    // Auto-remove info and warning messages after 5 seconds
    if (type === 'info' || type === 'warning') {
      setTimeout(() => {
        removeError(id);
      }, 5000);
    }

    return id;
  }, [maxErrors]);

  const removeError = useCallback((id: string) => {
    setErrors(prev => prev.filter(error => error.id !== id));
  }, []);

  const clearAllErrors = useCallback(() => {
    setErrors([]);
  }, []);

  return (
    <ErrorContext.Provider 
      value={{ 
        errors, 
        addError, 
        removeError, 
        clearAllErrors,
        networkStatus 
      }}
    >
      {children}
      <ErrorToastContainer />
    </ErrorContext.Provider>
  );
};

// Toast notification component
const ErrorToastContainer: React.FC = () => {
  const { errors, removeError } = useError();

  if (errors.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {errors.slice(0, 3).map(error => ( // Show only the 3 most recent
        <div
          key={error.id}
          className={`p-4 rounded-lg shadow-lg transition-all duration-300 transform ${
            error.type === 'error' 
              ? 'bg-red-900 border border-red-700 text-red-100'
              : error.type === 'warning'
              ? 'bg-yellow-900 border border-yellow-700 text-yellow-100'
              : 'bg-blue-900 border border-blue-700 text-blue-100'
          }`}
        >
          <div className="flex justify-between items-start">
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-lg">
                  {error.type === 'error' ? '🚨' : error.type === 'warning' ? '⚠️' : 'ℹ️'}
                </span>
                <span className="font-medium text-sm">
                  {error.type.toUpperCase()}
                </span>
                <span className="text-xs opacity-75">
                  {error.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <p className="text-sm break-words">{error.message}</p>
              {error.details && (
                <details className="mt-2">
                  <summary className="text-xs cursor-pointer opacity-75 hover:opacity-100">
                    Show details
                  </summary>
                  <p className="text-xs mt-1 opacity-75 font-mono bg-black bg-opacity-25 p-2 rounded">
                    {error.details}
                  </p>
                </details>
              )}
              {error.retryAction && (
                <button
                  onClick={error.retryAction}
                  className="mt-2 px-3 py-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-xs transition-colors"
                >
                  Retry
                </button>
              )}
            </div>
            <button
              onClick={() => removeError(error.id)}
              className="ml-2 text-white hover:text-gray-300 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
      
      {errors.length > 3 && (
        <div className="text-center">
          <span className="text-sm text-gray-400">
            +{errors.length - 3} more errors
          </span>
        </div>
      )}
    </div>
  );
};

// Hook for handling API errors
export const useAPIError = () => {
  const { addError, networkStatus } = useError();

  const handleAPIError = useCallback((
    error: any, 
    context: string, 
    retryAction?: () => void
  ) => {
    if (!networkStatus.isOnline) {
      addError(
        'No internet connection. Please check your network.',
        'error',
        `Context: ${context}`,
        retryAction
      );
      return;
    }

    let message = `Error in ${context}`;
    let details = '';

    if (error.message) {
      if (error.message.includes('timeout')) {
        message = `Request timeout for ${context}`;
        details = 'The server may be overloaded. Please try again.';
      } else if (error.message.includes('404')) {
        message = `Data not found for ${context}`;
        details = 'The requested resource may not exist.';
      } else if (error.message.includes('500')) {
        message = `Server error in ${context}`;
        details = 'Please try again later.';
      } else {
        message = error.message;
        details = `Context: ${context}`;
      }
    }

    addError(message, 'error', details, retryAction);
  }, [addError, networkStatus.isOnline]);

  return { handleAPIError };
};

export default ErrorProvider;
