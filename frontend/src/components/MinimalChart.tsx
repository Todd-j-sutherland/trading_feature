import React, { useEffect, useRef, useState } from 'react';
import { createChart, Time, ColorType } from 'lightweight-charts';

interface MinimalChartProps {
  symbol: string;
}

const MinimalChart: React.FC<MinimalChartProps> = ({ symbol }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const [status, setStatus] = useState<string>('Initializing...');
  const [apiData, setApiData] = useState<any>(null);

  // Fetch real data from API
  useEffect(() => {
    const fetchRealData = async () => {
      setStatus('🔄 Fetching real OHLCV data...');
      try {
        const response = await fetch(`/api/banks/${symbol}/ohlcv?period=1D`);
        const data = await response.json();
        
        if (data.success && data.data && data.data.length > 0) {
          setStatus(`✅ Fetched ${data.data.length} real data points`);
          setApiData(data.data);
        } else {
          setStatus('❌ No real data available - API returned empty');
          setApiData(null);
        }
      } catch (error) {
        setStatus(`❌ API Error: ${error}`);
        setApiData(null);
      }
    };

    fetchRealData();
  }, [symbol]);

  // Create chart with real data
  useEffect(() => {
    console.log('🔄 MinimalChart chart creation useEffect triggered');
    
    if (!chartContainerRef.current) {
      setStatus('❌ No container ref');
      return;
    }

    // Clean up existing chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    setStatus('🧪 Testing chart rendering...');
    
    try {
      const chart = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: 400,
        layout: { 
          textColor: 'white', 
          background: { type: ColorType.Solid, color: '#1a1a1a' } 
        }
      });

      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#00C851',
        downColor: '#FF4444',
        borderUpColor: '#00C851',
        borderDownColor: '#FF4444',
        wickUpColor: '#00C851',
        wickDownColor: '#FF4444',
      });

      // Always test with minimal data first
      const now = Math.floor(Date.now() / 1000);
      const testData = [
        { time: (now - 3600) as Time, open: 170, high: 175, low: 165, close: 172 },
        { time: (now - 1800) as Time, open: 172, high: 178, low: 168, close: 174 },
        { time: now as Time, open: 174, high: 176, low: 170, close: 173 }
      ];
      
      console.log('🧪 Setting test data to verify chart rendering:', testData);
      candlestickSeries.setData(testData);
      
      setStatus('✅ Test chart data rendered successfully');
      chartRef.current = chart;

      // Override with real data if available
      if (apiData && apiData.length > 0) {
        const realData = apiData.map((item: any) => ({
          time: item.timestamp as Time,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        })).sort((a: any, b: any) => a.time - b.time);

        console.log('📊 Replacing with real data:', realData.slice(0, 3));
        candlestickSeries.setData(realData);
        setStatus(`✅ Chart showing ${realData.length} REAL data points`);
      }

    } catch (error) {
      console.error('❌ Error creating chart:', error);
      setStatus(`❌ Chart Error: ${error}`);
    }

    // Cleanup
    return () => {
      if (chartRef.current) {
        console.log('🧹 Cleaning up chart');
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [apiData]);

  return (
    <div style={{ padding: '20px', background: '#1a1a1a', color: 'white' }}>
      <h3>📊 Minimal Chart Test for {symbol}</h3>
      <div style={{ 
        background: '#333', 
        padding: '10px', 
        borderRadius: '5px', 
        marginBottom: '20px',
        fontFamily: 'monospace' 
      }}>
        Status: {status}
      </div>
      <div 
        ref={chartContainerRef} 
        style={{ 
          width: '100%', 
          height: '400px',
          background: '#1a1a1a',
          border: '1px solid #333',
          borderRadius: '5px'
        }} 
      />
      {apiData && (
        <div style={{ marginTop: '10px', fontSize: '12px', color: '#888' }}>
          Real data: {apiData.length} points loaded from API
        </div>
      )}
    </div>
  );
};

export default MinimalChart;

  
