import React, { useState, useCallback } from 'react';
import TradingChart from './components/TradingChart';
import BankSelector from './components/BankSelector';
import ChartErrorBoundary from './components/ChartErrorBoundary';
import ErrorProvider from './contexts/ErrorContext';
import SimpleMLDashboard from './components/SimpleMLDashboard';
import IntegratedMLDashboard from './components/IntegratedMLDashboard';
import MinimalChart from './components/MinimalChart';
import { ASX_BANKS } from './constants/trading.constants';

// Memoized components for better performance
const MemoizedTradingChart = React.memo(TradingChart);
const MemoizedBankSelector = React.memo(BankSelector);

function App() {
  const [selectedBank, setSelectedBank] = useState(ASX_BANKS[0]);
  const [timeframe, setTimeframe] = useState('1D');
  const [currentView, setCurrentView] = useState<'main' | 'ml-test' | 'integrated-ml' | 'minimal-test'>('main');

  // Memoized callbacks to prevent unnecessary re-renders
  const handleBankSelect = useCallback((bank: typeof ASX_BANKS[0]) => {
    setSelectedBank(bank);
  }, []);

  const handleTimeframeChange = useCallback((newTimeframe: string) => {
    setTimeframe(newTimeframe);
  }, []);

  return (
    <ErrorProvider maxErrors={5}>
      <div className="min-h-screen bg-gray-900 text-white">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 p-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">
              ASX Bank Trading Dashboardd
            </h1>
            <div className="flex items-center space-x-4">
              <div className="flex bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setCurrentView('main')}
                  className={`px-3 py-2 rounded-md text-sm transition-colors ${
                    currentView === 'main' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Main Dashboard
                </button>
                <button
                  onClick={() => setCurrentView('integrated-ml')}
                  className={`px-3 py-2 rounded-md text-sm transition-colors ${
                    currentView === 'integrated-ml' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  🧠 Integrated ML dd
                </button>
                <button
                  onClick={() => setCurrentView('minimal-test')}
                  className={`px-3 py-2 rounded-md text-sm transition-colors ${
                    currentView === 'minimal-test' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Hello Todd
                  🔧 Chart Test
                </button>
                <button
                  onClick={() => setCurrentView('ml-test')}
                  className={`px-3 py-2 rounded-md text-sm transition-colors ${
                    currentView === 'ml-test' 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  🤖 ML Test
                </button>
              </div>
              
              <span className="text-sm text-gray-400">
                Live ML Sentiment Analysis
              </span>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </header>

        {/* Conditional Content Based on Current View */}
        {currentView === 'main' ? (
          <>
            {/* Main Content */}
            <main className="max-w-7xl mx-auto p-4">
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                
                {/* Bank Selector */}
                <div className="lg:col-span-1">
                  <MemoizedBankSelector
                    banks={ASX_BANKS}
                    selectedBank={selectedBank}
                    onSelectBank={handleBankSelect}
                    timeframe={timeframe}
                    onTimeframeChange={handleTimeframeChange}
                  />
                </div>

                {/* Main Chart Area */}
                <div className="lg:col-span-3">
                  <div className="bg-gray-800 rounded-lg p-6">
                    <div className="mb-4">
                      <h2 className="text-xl font-semibold text-white">
                        {selectedBank.name} ({selectedBank.code})
                      </h2>
                      <p className="text-gray-400">{selectedBank.sector}</p>
                    </div>
                    
                    <ChartErrorBoundary 
                      showDetails={process.env.NODE_ENV === 'development'}
                      onRetry={() => handleTimeframeChange(timeframe)}
                    >
                      <MemoizedTradingChart 
                        symbol={selectedBank.code}
                        timeframe={timeframe}
                      />
                    </ChartErrorBoundary>
                  </div>
                </div>
              </div>

              {/* Enhanced ML Insights Panel */}
              <div className="mt-6 bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <span className="mr-2">🤖</span>
                  ML Sentiment Analysis
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-lg p-4 border border-green-700">
                    <h4 className="text-sm font-medium text-green-300 mb-2">Current Signal</h4>
                    <p className="text-2xl font-bold text-green-400">BUY</p>
                    <div className="text-xs text-green-300 mt-1">Strong uptrend</div>
                  </div>
                  <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-lg p-4 border border-blue-700">
                    <h4 className="text-sm font-medium text-blue-300 mb-2">Confidence</h4>
                    <p className="text-2xl font-bold text-blue-400">78%</p>
                    <div className="w-full bg-blue-900 rounded-full h-2 mt-2">
                      <div className="bg-blue-400 h-2 rounded-full" style={{ width: '78%' }}></div>
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-lg p-4 border border-purple-700">
                    <h4 className="text-sm font-medium text-purple-300 mb-2">Sentiment Score</h4>
                    <p className="text-2xl font-bold text-purple-400">+0.23</p>
                    <div className="text-xs text-purple-300 mt-1">Bullish sentiment</div>
                  </div>
                  <div className="bg-gradient-to-br from-amber-900 to-amber-800 rounded-lg p-4 border border-amber-700">
                    <h4 className="text-sm font-medium text-amber-300 mb-2">Market Status</h4>
                    <p className="text-lg font-bold text-amber-400">OPEN</p>
                    <div className="text-xs text-amber-300 mt-1">Active trading</div>
                  </div>
                </div>
              </div>
            </main>
          </>
        ) : currentView === 'integrated-ml' ? (
          /* Integrated ML Dashboard - Uses Real ML Training Pipeline */
          <IntegratedMLDashboard />
        ) : currentView === 'minimal-test' ? (
          /* Minimal Chart Test */
          <div className="max-w-7xl mx-auto p-4">
            <MinimalChart symbol={selectedBank.code} />
          </div>
        ) : (
          /* Simple ML Test Dashboard */
          <SimpleMLDashboard />
        )}
      </div>
    </ErrorProvider>
  );
}

export default App;
