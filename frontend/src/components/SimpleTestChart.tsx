import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const SimpleTestChart: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    console.log('🔄 SimpleTestChart useEffect triggered');
    
    if (!chartContainerRef.current) {
      console.log('❌ No container ref');
      return;
    }

    if (chartRef.current) {
      console.log('✅ Chart already exists');
      return;
    }

    console.log('📊 Creating simple test chart...', {
      containerWidth: chartContainerRef.current.clientWidth,
      containerHeight: chartContainerRef.current.clientHeight
    });

    try {
      const chart = createChart(chartContainerRef.current, {
        width: 800,
        height: 400,
        layout: {
          background: { color: '#1a1a1a' },
          textColor: '#d1d4dc',
        },
        grid: {
          vertLines: { color: '#2B2B43' },
          horzLines: { color: '#2B2B43' },
        },
      });

      chartRef.current = chart;
      console.log('✅ Chart created successfully');

      // Add a simple candlestick series
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#00C851',
        downColor: '#FF4444',
        borderUpColor: '#00C851',
        borderDownColor: '#FF4444',
        wickUpColor: '#00C851',
        wickDownColor: '#FF4444',
      });

      // Add simple test data
      const testData = [
        { time: '2024-01-01', open: 100, high: 110, low: 95, close: 105 },
        { time: '2024-01-02', open: 105, high: 115, low: 100, close: 108 },
        { time: '2024-01-03', open: 108, high: 120, low: 105, close: 115 },
        { time: '2024-01-04', open: 115, high: 125, low: 110, close: 118 },
        { time: '2024-01-05', open: 118, high: 130, low: 115, close: 122 },
      ];

      candlestickSeries.setData(testData);
      console.log('✅ Test data added to chart');

    } catch (error) {
      console.error('❌ Error creating simple test chart:', error);
    }

    // Cleanup function
    return () => {
      if (chartRef.current) {
        console.log('🧹 Cleaning up simple test chart');
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-white text-xl mb-4">Simple Chart Test</h2>
      <div
        ref={chartContainerRef}
        style={{
          width: '800px',
          height: '400px',
          backgroundColor: '#1a1a1a',
          border: '2px solid #00ff00',
        }}
      >
        <div style={{ color: 'white', padding: '10px' }}>
          Chart Container: {chartContainerRef.current?.clientWidth}x{chartContainerRef.current?.clientHeight}
          {chartRef.current ? ' ✅ Chart Created' : ' ❌ No Chart'}
        </div>
      </div>
    </div>
  );
};

export default SimpleTestChart;
