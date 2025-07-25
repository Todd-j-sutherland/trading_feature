import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, LineStyle, Time, CrosshairMode, SeriesMarker } from 'lightweight-charts';
import { CHART_COLORS } from '../constants/trading.constants';
import { useChartData } from '../hooks/useChartData';
import { useMLPredictions } from '../hooks/useMLPredictions';
import { formatChartTime, getCurrentAustralianTime, getMarketStatus } from '../utils/timeUtils';

interface TradingChartProps {
  symbol: string;
  timeframe: string;
}

// Timeframe configuration for hourly and other intervals
const TIMEFRAME_CONFIG = {
  '1H': { interval: 3600, label: '1 Hour', dataPoints: 168 }, // 1 week of hourly data
  '1D': { interval: 86400, label: '1 Day', dataPoints: 30 },   // 30 days
  '1W': { interval: 604800, label: '1 Week', dataPoints: 52 }, // 52 weeks
  '1M': { interval: 2592000, label: '1 Month', dataPoints: 12 } // 12 months
};

const TradingChart: React.FC<TradingChartProps> = ({ symbol, timeframe }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const priceSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sentimentSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Custom hooks for data fetching
  const { chartData, loading: chartLoading } = useChartData(symbol, timeframe);
  const { mlPredictions, loading: mlLoading, stats } = useMLPredictions(symbol, timeframe);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Enhanced chart configuration for professional trading interface
    const chartOptions = {
      layout: {
        background: { color: CHART_COLORS.background },
        textColor: CHART_COLORS.text,
      },
      grid: {
        vertLines: { color: CHART_COLORS.grid },
        horzLines: { color: CHART_COLORS.grid },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: CHART_COLORS.grid,
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: CHART_COLORS.grid,
        timeVisible: true,
        secondsVisible: timeframe === '1H', // Show seconds only for hourly
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: 500, // Increased height for better visibility
    };

    const chart = createChart(chartContainerRef.current, chartOptions);

    chartRef.current = chart;

    // Add price series (main chart)
    const priceSeries = chart.addLineSeries({
      color: '#2196F3',
      lineWidth: 2,
      title: `${symbol} Price`,
    });
    priceSeriesRef.current = priceSeries;

    // Add sentiment series (separate pane)
    const sentimentSeries = chart.addLineSeries({
      color: CHART_COLORS.sentiment,
      lineWidth: 2,
      title: 'ML Sentiment',
      priceScaleId: 'sentiment',
    });
    sentimentSeriesRef.current = sentimentSeries;

    // Configure sentiment price scale
    chart.priceScale('sentiment').applyOptions({
      scaleMargins: {
        top: 0.7,
        bottom: 0,
      },
      borderColor: CHART_COLORS.grid,
    });

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [symbol, timeframe]);

  // Load data when chart is ready
  useEffect(() => {
    if (chartRef.current && !chartLoading && !mlLoading) {
      loadChartData();
    }
  }, [chartData, mlPredictions, chartLoading, mlLoading]);

  const loadChartData = () => {
    if (!priceSeriesRef.current || !sentimentSeriesRef.current) return;

    setIsLoading(true);

    try {
      // Use real data if available, otherwise generate sample data
      if (chartData && chartData.length > 0) {
        // Sort chart data by timestamp in ascending order
        const sortedChartData = [...chartData].sort((a, b) => a.timestamp - b.timestamp);
        
        // Transform real OHLCV data to line data
        const priceData = sortedChartData.map(item => ({
          time: item.timestamp as Time,
          value: item.close,
        }));
        
        priceSeriesRef.current.setData(priceData);
      } else {
        // Generate sample data based on timeframe
        const samplePriceData = generateSamplePriceData();
        priceSeriesRef.current.setData(samplePriceData);
      }

      // Load ML sentiment data
      if (mlPredictions && mlPredictions.length > 0) {
        // Sort data by time in ascending order (TradingView requirement)
        const sortedPredictions = [...mlPredictions].sort((a, b) => a.time - b.time);
        
        const sentimentData = sortedPredictions.map(pred => ({
          time: pred.time as Time,
          value: pred.sentimentScore,
        }));
        
        sentimentSeriesRef.current.setData(sentimentData);

        // Add prediction markers for high confidence signals
        const markers = createPredictionMarkers(sortedPredictions);
        priceSeriesRef.current.setMarkers(markers);
      } else {
        // Generate sample sentiment data
        const sampleSentimentData = generateSampleSentimentData();
        sentimentSeriesRef.current.setData(sampleSentimentData);
        
        // Add sample markers
        const sampleMarkers = generateSampleMarkers();
        priceSeriesRef.current.setMarkers(sampleMarkers);
      }

    } catch (error) {
      console.error('Error loading chart data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateSamplePriceData = () => {
    const config = TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG] || TIMEFRAME_CONFIG['1D'];
    const data = [];
    const now = new Date();
    
    for (let i = 0; i < config.dataPoints; i++) {
      const time = new Date(now.getTime() - (config.dataPoints - 1 - i) * config.interval * 1000);
      const timestamp = Math.floor(time.getTime() / 1000) as Time;
      
      // Generate realistic price movement
      const basePrice = 118; // CBA base price
      const trend = Math.sin((i / config.dataPoints) * Math.PI * 2) * 3;
      const noise = (Math.random() - 0.5) * 2;
      const price = basePrice + trend + noise;
      
      data.push({
        time: timestamp,
        value: Math.max(price, 110), // Minimum price floor
      });
    }
    
    return data;
  };

  const generateSampleSentimentData = () => {
    const config = TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG] || TIMEFRAME_CONFIG['1D'];
    const data = [];
    const now = new Date();
    
    for (let i = 0; i < config.dataPoints; i++) {
      const time = new Date(now.getTime() - (config.dataPoints - 1 - i) * config.interval * 1000);
      const timestamp = Math.floor(time.getTime() / 1000) as Time;
      
      // Generate sentiment between -1 and 1
      const sentiment = Math.sin((i / config.dataPoints) * Math.PI * 4) * 0.4 + 
                       (Math.random() - 0.5) * 0.3;
      
      data.push({
        time: timestamp,
        value: Math.max(-1, Math.min(1, sentiment)),
      });
    }
    
    return data;
  };

  const generateSampleMarkers = () => {
    const config = TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG] || TIMEFRAME_CONFIG['1D'];
    const now = new Date();
    const markers: Array<{
      time: Time;
      position: 'belowBar' | 'aboveBar';
      color: string;
      shape: 'arrowUp' | 'arrowDown';
      text: string;
      size: number;
    }> = [];

    // Add a few sample signals
    const signalPoints = [
      Math.floor(config.dataPoints * 0.3),
      Math.floor(config.dataPoints * 0.7),
      Math.floor(config.dataPoints * 0.9)
    ];

    signalPoints.forEach((point, index) => {
      const time = new Date(now.getTime() - (config.dataPoints - 1 - point) * config.interval * 1000);
      const timestamp = Math.floor(time.getTime() / 1000) as Time;
      
      const isBuy = index % 2 === 0;
      markers.push({
        time: timestamp,
        position: isBuy ? 'belowBar' as const : 'aboveBar' as const,
        color: isBuy ? CHART_COLORS.buySignal : CHART_COLORS.sellSignal,
        shape: isBuy ? 'arrowUp' as const : 'arrowDown' as const,
        text: `${isBuy ? 'BUY' : 'SELL'} (${(0.6 + Math.random() * 0.3).toFixed(2)})`,
        size: 1,
      });
    });

    return markers;
  };

  const createPredictionMarkers = (predictions: any[]) => {
    return predictions
      .filter(pred => pred.confidence > 0.7) // Only show high confidence predictions
      .map(pred => {
        // Determine signal based on sentiment score
        const signal = pred.sentimentScore > 0.3 ? 'BUY' : pred.sentimentScore < -0.3 ? 'SELL' : null;
        
        if (!signal) return null;
        
        return {
          time: pred.time as Time,
          position: signal === 'BUY' ? 'belowBar' as const : 'aboveBar' as const,
          color: signal === 'BUY' ? CHART_COLORS.buySignal : CHART_COLORS.sellSignal,
          shape: signal === 'BUY' ? 'arrowUp' as const : 'arrowDown' as const,
          text: `${signal} (${pred.confidence.toFixed(2)})`,
          size: pred.confidence > 0.8 ? 2 : 1,
        };
      })
      .filter(marker => marker !== null);
  };

  return (
    <div className="w-full">
      {/* Chart Header */}
      <div className="mb-4 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold text-white">
            {symbol} - {TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG]?.label || timeframe}
          </h3>
          <div className="flex items-center space-x-4 text-sm text-gray-400">
            <span>Price Chart with ML Sentiment Analysis</span>
            <span>•</span>
            <span className="text-blue-400">{getMarketStatus()}</span>
            <span>•</span>
            <span>{getCurrentAustralianTime()}</span>
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex space-x-4 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 rounded mr-2"></div>
            <span className="text-gray-300">Price</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
            <span className="text-gray-300">ML Sentiment</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-500 rounded mr-2"></div>
            <span className="text-gray-300">Signals</span>
          </div>
        </div>
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute top-4 right-4 bg-blue-600 text-white px-3 py-1 rounded text-sm">
          Loading {timeframe} data...
        </div>
      )}
      
      {/* Chart Container */}
      <div 
        ref={chartContainerRef}
        className="chart-container w-full h-96 rounded-lg border border-gray-700"
        style={{ backgroundColor: CHART_COLORS.background }}
      />
      
      {/* Chart Info */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="bg-gray-800 p-3 rounded">
          <h4 className="text-gray-300 font-medium mb-1">Timeframe</h4>
          <p className="text-white">{TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG]?.label || timeframe}</p>
        </div>
        
        <div className="bg-gray-800 p-3 rounded">
          <h4 className="text-gray-300 font-medium mb-1">Data Points</h4>
          <p className="text-white">{TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG]?.dataPoints || 'N/A'}</p>
        </div>
        
        <div className="bg-gray-800 p-3 rounded">
          <h4 className="text-gray-300 font-medium mb-1">Status</h4>
          <p className="text-green-400">
            {isLoading ? 'Loading...' : (mlPredictions.length > 0 ? 'Live ML Data' : 'Sample Data')}
          </p>
        </div>
      </div>

      {/* ML Data Quality Stats */}
      {stats && (
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-gray-800 p-3 rounded">
            <h4 className="text-gray-300 font-medium mb-1">Total Records</h4>
            <p className="text-white">{stats.total_records}</p>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <h4 className="text-gray-300 font-medium mb-1">Technical Score</h4>
            <p className="text-white">{stats.records_with_technical}/{stats.total_records}</p>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <h4 className="text-gray-300 font-medium mb-1">Reddit Data</h4>
            <p className="text-white">{stats.records_with_reddit}/{stats.total_records}</p>
          </div>
          <div className="bg-gray-800 p-3 rounded">
            <h4 className="text-gray-300 font-medium mb-1">Avg Confidence</h4>
            <p className="text-white">{(stats.avg_confidence * 100).toFixed(1)}%</p>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-4 text-sm text-gray-400 space-y-1">
        <p>• All times displayed in Australian Eastern Time (AEST/AEDT)</p>
        <p>• Hover over the chart to see detailed information at any point</p>
        <p>• Green arrows indicate BUY signals, red arrows indicate SELL signals</p>
        <p>• Sentiment oscillator shows ML prediction confidence (-1 bearish to +1 bullish)</p>
        <p>• {timeframe === '1H' ? 'Hourly data provides intraday trading insights with 168 data points (1 week)' : `${timeframe} timeframe shows ${TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG]?.label.toLowerCase()} trends`}</p>
        <p>• ASX trading hours: 10:00 AM - 4:00 PM AEST, Monday to Friday</p>
      </div>
    </div>
  );
};

export default TradingChart;
