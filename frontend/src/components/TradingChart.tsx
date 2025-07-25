import React, { useEffect, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi, LineStyle, Time } from 'lightweight-charts';
import { CHART_COLORS } from '../constants/trading.constants';

interface TradingChartProps {
  symbol: string;
  timeframe: string;
}

const TradingChart: React.FC<TradingChartProps> = ({ symbol, timeframe }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const priceSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sentimentSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create the main chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: CHART_COLORS.background },
        textColor: CHART_COLORS.text,
      },
      grid: {
        vertLines: { color: CHART_COLORS.grid },
        horzLines: { color: CHART_COLORS.grid },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: CHART_COLORS.grid,
      },
    });

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

    // Generate sample data for now
    generateSampleData();

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

  const generateSampleData = () => {
    if (!priceSeriesRef.current || !sentimentSeriesRef.current) return;

    // Generate sample price data
    const priceData = [];
    const sentimentData = [];
    const now = new Date();
    
    for (let i = 0; i <= 30; i++) {
      const time = new Date(now.getTime() - (30 - i) * 24 * 60 * 60 * 1000);
      const timestamp = Math.floor(time.getTime() / 1000) as Time;
      
      // Sample price data (around $118 for CBA)
      const price = 118 + Math.sin(i * 0.3) * 5 + Math.random() * 2;
      
      // Sample sentiment data (-1 to +1)
      const sentiment = Math.sin(i * 0.2) * 0.5 + Math.random() * 0.4 - 0.2;
      
      priceData.push({
        time: timestamp,
        value: price,
      });
      
      sentimentData.push({
        time: timestamp,
        value: sentiment,
      });
    }

    priceSeriesRef.current.setData(priceData);
    sentimentSeriesRef.current.setData(sentimentData);

    // Add some sample markers (ensure ascending order)
    const markers = [
      {
        time: Math.floor((now.getTime() - 15 * 24 * 60 * 60 * 1000) / 1000) as Time,
        position: 'aboveBar' as const,
        color: CHART_COLORS.sellSignal,
        shape: 'arrowDown' as const,
        text: 'SELL (0.72)',
      },
      {
        time: Math.floor((now.getTime() - 5 * 24 * 60 * 60 * 1000) / 1000) as Time,
        position: 'belowBar' as const,
        color: CHART_COLORS.buySignal,
        shape: 'arrowUp' as const,
        text: 'BUY (0.85)',
      },
    ];

    priceSeriesRef.current.setMarkers(markers);
  };

  return (
    <div className="w-full">
      <div className="mb-4 flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">
          Price Chart with ML Sentiment
        </h3>
        <div className="flex space-x-2 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 rounded mr-2"></div>
            <span className="text-gray-300">Price</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
            <span className="text-gray-300">Sentiment</span>
          </div>
        </div>
      </div>
      
      <div 
        ref={chartContainerRef}
        className="chart-container w-full h-96 rounded-lg"
        style={{ backgroundColor: CHART_COLORS.background }}
      />
      
      <div className="mt-4 text-sm text-gray-400">
        <p>Green arrows indicate BUY signals, red arrows indicate SELL signals.</p>
        <p>Sentiment oscillator ranges from -1 (very bearish) to +1 (very bullish).</p>
      </div>
    </div>
  );
};

export default TradingChart;
