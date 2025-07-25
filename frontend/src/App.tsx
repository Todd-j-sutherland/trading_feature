import { useState, useEffect } from 'react';
import TradingChart from './components/TradingChart';
import BankSelector from './components/BankSelector';
import { ASX_BANKS } from './constants/trading.constants';

function App() {
  const [selectedBank, setSelectedBank] = useState(ASX_BANKS[0]);
  const [timeframe, setTimeframe] = useState('1D');

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">
            ASX Bank Trading Dashboard
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-400">
              Live ML Sentiment Analysis
            </span>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Bank Selector */}
          <div className="lg:col-span-1">
            <BankSelector
              banks={ASX_BANKS}
              selectedBank={selectedBank}
              onSelectBank={setSelectedBank}
              timeframe={timeframe}
              onTimeframeChange={setTimeframe}
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
              
              <TradingChart 
                symbol={selectedBank.code}
                timeframe={timeframe}
              />
            </div>
          </div>
        </div>

        {/* ML Insights Panel - Simple for now */}
        <div className="mt-6 bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">ML Sentiment Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-700 rounded p-4">
              <h4 className="text-sm font-medium text-gray-300">Current Signal</h4>
              <p className="text-2xl font-bold text-buy-signal">BUY</p>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <h4 className="text-sm font-medium text-gray-300">Confidence</h4>
              <p className="text-2xl font-bold text-white">78%</p>
            </div>
            <div className="bg-gray-700 rounded p-4">
              <h4 className="text-sm font-medium text-gray-300">Sentiment Score</h4>
              <p className="text-2xl font-bold text-white">+0.23</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
