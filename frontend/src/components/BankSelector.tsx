import React from 'react';
import { BankSymbol } from '../types/trading.types';
import { TIMEFRAMES } from '../constants/trading.constants';

interface BankSelectorProps {
  banks: BankSymbol[];
  selectedBank: BankSymbol;
  onSelectBank: (bank: BankSymbol) => void;
  timeframe: string;
  onTimeframeChange: (timeframe: string) => void;
}

const BankSelector: React.FC<BankSelectorProps> = ({
  banks,
  selectedBank,
  onSelectBank,
  timeframe,
  onTimeframeChange
}) => {
  return (
    <div className="space-y-6">
      {/* Bank Selection */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4 text-white">Select Bank</h3>
        <div className="space-y-2">
          {banks.map((bank) => (
            <button
              key={bank.code}
              onClick={() => onSelectBank(bank)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                selectedBank.code === bank.code
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <div className="font-medium">{bank.code}</div>
              <div className="text-sm opacity-75">{bank.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Timeframe Selection */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4 text-white">Timeframe</h3>
        <div className="grid grid-cols-2 gap-2">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.value}
              onClick={() => onTimeframeChange(tf.value)}
              className={`p-2 rounded text-center transition-colors ${
                timeframe === tf.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Stats - Placeholder */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4 text-white">Quick Stats</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-400">Last Price:</span>
            <span className="text-white">$118.50</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Change:</span>
            <span className="text-green-500">+1.2%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Volume:</span>
            <span className="text-white">2.1M</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BankSelector;
