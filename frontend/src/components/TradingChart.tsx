import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { createChart, IChartApi, ISeriesApi, Time, CrosshairMode, CandlestickData, HistogramData } from 'lightweight-charts';
import { CHART_COLORS } from '../constants/trading.constants';
import { useChartData } from '../hooks/useChartData';
import { useOriginalMLPredictions } from '../hooks/useOriginalMLPredictions';
import { useLivePriceData, useLiveMLPredictions } from '../services/liveMlService';
import { getCurrentAustralianTime, getMarketStatus } from '../utils/timeUtils';

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
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const sentimentSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [forceUpdate, setForceUpdate] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [lastPriceTimestamp, setLastPriceTimestamp] = useState<number>(0);
  const [lastMLTimestamp, setLastMLTimestamp] = useState<number>(0);

  // Real-time data hooks
  const { priceData: livePriceData, isConnected } = useLivePriceData(symbol);
  const { prediction: liveMLPrediction, isLive } = useLiveMLPredictions(symbol);

  // Destructure errors from hooks
  const { chartData, loading: chartLoading, error: chartError } = useChartData(symbol, timeframe);
  const { mlPredictions, loading: mlLoading, stats, error: mlError } = useOriginalMLPredictions(symbol, timeframe);

  // Utility function to ensure valid timestamp
  const ensureValidTimestamp = (timestamp: number): number => {
    // Convert to seconds if it's in milliseconds
    const ts = timestamp > 1e10 ? Math.floor(timestamp / 1000) : timestamp;
    // Ensure it's a valid number
    return isNaN(ts) || ts <= 0 ? Math.floor(Date.now() / 1000) : ts;
  };

  // Zoom control functions
  const handleZoomIn = () => {
    if (chartRef.current) {
      const timeScale = chartRef.current.timeScale();
      const visibleRange = timeScale.getVisibleRange();
      
      if (visibleRange) {
        const fromTime = visibleRange.from as number;
        const toTime = visibleRange.to as number;
        const centerTime = (fromTime + toTime) / 2;
        const currentRange = toTime - fromTime;
        
        // Prevent over-zooming (minimum range of 1 hour)
        const minRange = 3600; // 1 hour in seconds
        if (currentRange > minRange) {
          const newRange = Math.max(currentRange * 0.8, minRange); // Zoom in by 20%
          
          timeScale.setVisibleRange({
            from: (centerTime - newRange / 2) as Time,
            to: (centerTime + newRange / 2) as Time,
          });
        }
      }
    }
  };

  const handleZoomOut = () => {
    if (chartRef.current) {
      const timeScale = chartRef.current.timeScale();
      const visibleRange = timeScale.getVisibleRange();
      
      if (visibleRange) {
        const fromTime = visibleRange.from as number;
        const toTime = visibleRange.to as number;
        const centerTime = (fromTime + toTime) / 2;
        const currentRange = toTime - fromTime;
        
        // Prevent over-zooming out (maximum range of 1 year)
        const maxRange = 365 * 24 * 3600; // 1 year in seconds
        if (currentRange < maxRange) {
          const newRange = Math.min(currentRange * 1.25, maxRange); // Zoom out by 25%
          
          timeScale.setVisibleRange({
            from: (centerTime - newRange / 2) as Time,
            to: (centerTime + newRange / 2) as Time,
          });
        }
      }
    }
  };

  const handleResetZoom = () => {
    if (chartRef.current) {
      chartRef.current.timeScale().resetTimeScale();
    }
  };

  const handleFitToData = () => {
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  };

  // Create chart instance only once when component mounts
  useEffect(() => {
    console.log('🔄 Chart creation useEffect triggered');
    
    if (!chartContainerRef.current) {
      console.log('🚫 No container ref available');
      return;
    }
    
    if (chartRef.current) {
      console.log('🚫 Chart already exists');
      return;
    }

    console.log('📊 Creating chart with container:', {
      containerWidth: chartContainerRef.current.clientWidth,
      containerHeight: chartContainerRef.current.clientHeight,
      containerElement: chartContainerRef.current
    });

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
          top: 0.05,
          bottom: 0.05,
        },
        visible: true,
        entireTextOnly: false,
        // Enable vertical scrolling/zooming
        mode: 2, // Normal mode with scaling
        invertScale: false,
        alignLabels: true,
        borderVisible: true,
        // Allow mouse wheel scrolling for vertical zoom
        handleScroll: {
          mouseWheel: true,
          pressedMouseMove: true,
          horzTouchDrag: true,
          vertTouchDrag: true,
        },
      },
      timeScale: {
        borderColor: CHART_COLORS.grid,
        timeVisible: true,
        secondsVisible: false, // Will be updated dynamically
        fixLeftEdge: false,
        fixRightEdge: false,
        lockVisibleTimeRangeOnResize: false,
        rightBarStaysOnScroll: true,
        barSpacing: 6,
        minBarSpacing: 3,
        visible: true,
        // Enable horizontal scrolling
        allowShiftVisibleRangeOnWhitespaceClick: true,
        allowBoldLabels: true,
        shiftVisibleRangeOnNewBar: true,
      },
      // Add mouse wheel and touch handling for better scrolling
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      // Enable kinetic scrolling
      kineticScroll: {
        touch: true,
        mouse: true,
      },
      width: chartContainerRef.current.clientWidth,
      height: Math.max(500, Math.min(800, chartContainerRef.current.clientHeight || 500)),
      autoSize: true,
    };

    console.log('📊 Chart options prepared:', chartOptions);

    try {
      const chart = createChart(chartContainerRef.current, chartOptions);
      console.log('✅ Chart instance created:', chart);
      chartRef.current = chart;

      console.log('📊 Chart created, adding series...');

      // Add candlestick series (main chart)
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#00C851',
        downColor: '#FF4444',
        borderUpColor: '#00C851',
        borderDownColor: '#FF4444',
        wickUpColor: '#00C851',
        wickDownColor: '#FF4444',
      });
      candlestickSeriesRef.current = candlestickSeries;

      // Add volume series
      const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: 'volume',
      });
      volumeSeriesRef.current = volumeSeries;

      // Configure volume price scale with more space
      try {
        chart.priceScale('volume').applyOptions({
          scaleMargins: {
            top: 0.75,
            bottom: 0.05,
          },
          visible: true,
        });
      } catch (error) {
        console.warn('Error configuring volume price scale:', error);
      }

      // Add sentiment series (separate pane with more spacing)
      const sentimentSeries = chart.addLineSeries({
        color: CHART_COLORS.sentiment,
        lineWidth: 2,
        title: 'ML Sentiment',
        priceScaleId: 'sentiment',
      });
      sentimentSeriesRef.current = sentimentSeries;

      console.log('📊 All series added:', {
        candlestick: !!candlestickSeriesRef.current,
        volume: !!volumeSeriesRef.current,
        sentiment: !!sentimentSeriesRef.current
      });

      // IMMEDIATE SAMPLE DATA LOAD - to test chart rendering
      console.log('🚀 Loading immediate sample data...');
      setTimeout(() => {
        try {
          const sampleCandlestickData = generateSampleCandlestickData();
          const sampleVolumeData = generateSampleVolumeData();
          const sampleSentimentData = generateSampleSentimentData();
          const sampleMarkers = generateSampleMarkers();
          
          console.log('🚀 Setting sample data:', {
            candleCount: sampleCandlestickData.length,
            volumeCount: sampleVolumeData.length,
            sentimentCount: sampleSentimentData.length,
            markersCount: sampleMarkers.length
          });
          
          candlestickSeries.setData(sampleCandlestickData);
          volumeSeries.setData(sampleVolumeData);
          sentimentSeries.setData(sampleSentimentData);
          candlestickSeries.setMarkers(sampleMarkers);
          
          console.log('✅ Sample data loaded successfully!');
          setIsLoading(false);
        } catch (error) {
          console.error('❌ Error loading sample data:', error);
        }
      }, 100); // Load sample data almost immediately

    } catch (error) {
      console.error('❌ Error creating chart:', error);
      return;
    }

    const chart = chartRef.current; // Get reference for cleanup

    // Configure sentiment price scale (after series is created)
    try {
      chart.priceScale('sentiment').applyOptions({
        scaleMargins: {
          top: 0.85,
          bottom: 0.05,
        },
        visible: true,
        borderColor: CHART_COLORS.grid,
      });
    } catch (error) {
      console.warn('Error configuring sentiment price scale:', error);
    }

    // Add enhanced vertical scrolling capabilities
    console.log('🎯 Setting up enhanced scrolling controls...');
    
    // Add keyboard event handlers for vertical scrolling
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!chart) return;
      
      const priceScale = chart.priceScale('right');
      
      switch (event.key) {
        case 'ArrowUp':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            // Zoom in vertically by scaling the price range
            console.log('🔍 Zooming in vertically');
            priceScale.applyOptions({ 
              scaleMargins: { top: 0.1, bottom: 0.1 } // Tighter margins for zoom in
            });
          }
          break;
          
        case 'ArrowDown':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            // Zoom out vertically by expanding the price range
            console.log('🔍 Zooming out vertically');
            priceScale.applyOptions({ 
              scaleMargins: { top: 0.02, bottom: 0.02 } // Wider margins for zoom out
            });
          }
          break;
          
        case 'Home':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            // Reset vertical zoom and pan to fit all data
            console.log('🏠 Resetting vertical zoom and pan');
            accumulatedPanY = 0; // Reset accumulated mouse pan
            accumulatedTouchPanY = 0; // Reset accumulated touch pan
            priceScale.applyOptions({ 
              autoScale: true,
              scaleMargins: { top: 0.05, bottom: 0.05 }
            });
          }
          break;
          
        case 'PageUp':
          event.preventDefault();
          // Pan up (show higher prices)
          console.log('⬆️ Panning up');
          break;
          
        case 'PageDown':
          event.preventDefault();
          // Pan down (show lower prices)
          console.log('⬇️ Panning down');
          break;
      }
    };

    // Add enhanced wheel/trackpad event handler for vertical scrolling
    const handleWheel = (event: WheelEvent) => {
      if (!chart) return;
      
      const priceScale = chart.priceScale('right');
      
      // Detect trackpad vs mouse wheel
      const isTrackpad = Math.abs(event.deltaY) < 50 && event.deltaMode === 0;
      const isTouchpad = event.deltaX !== 0 || Math.abs(event.deltaY) < 100;
      
      // Handle different scrolling modes
      if (event.shiftKey || (isTrackpad && Math.abs(event.deltaX) < Math.abs(event.deltaY))) {
        // Vertical scrolling for price scale zoom
        event.preventDefault();
        
        // Use different sensitivity for trackpad vs mouse wheel
        const sensitivity = isTrackpad ? 0.5 : 1.0;
        const deltaY = event.deltaY * sensitivity;
        
        if (deltaY > 0) {
          // Scroll down - zoom out
          console.log('🔍 Trackpad/Mouse wheel zoom out');
          priceScale.applyOptions({ 
            scaleMargins: { top: 0.02, bottom: 0.02 }
          });
        } else {
          // Scroll up - zoom in
          console.log('🔍 Trackpad/Mouse wheel zoom in');
          priceScale.applyOptions({ 
            scaleMargins: { top: 0.1, bottom: 0.1 }
          });
        }
        
        // Reset to auto-scale after a delay to recalculate proper margins
        setTimeout(() => {
          priceScale.applyOptions({ autoScale: true });
        }, 100);
      } 
      else if (isTouchpad && event.ctrlKey && Math.abs(event.deltaY) > 0) {
        // Pinch-to-zoom gesture on trackpad (Ctrl + scroll)
        event.preventDefault();
        
        const zoomSensitivity = 0.3;
        const deltaY = event.deltaY * zoomSensitivity;
        
        console.log('🤏 Trackpad pinch-to-zoom detected');
        
        if (deltaY > 0) {
          // Pinch out - zoom out
          priceScale.applyOptions({ 
            scaleMargins: { top: 0.01, bottom: 0.01 }
          });
        } else {
          // Pinch in - zoom in
          priceScale.applyOptions({ 
            scaleMargins: { top: 0.15, bottom: 0.15 }
          });
        }
        
        setTimeout(() => {
          priceScale.applyOptions({ autoScale: true });
        }, 150);
      }
    };

    // Add event listeners
    const container = chartContainerRef.current;
    container.addEventListener('keydown', handleKeyDown);
    container.addEventListener('wheel', handleWheel, { passive: false });
    
    // Add vertical drag panning support
    let isDragging = false;
    let lastDragY = 0;
    let accumulatedPanY = 0; // Track total pan offset
    
    const handleMouseDown = (event: MouseEvent) => {
      // Only start drag on right mouse button or Shift + left mouse button
      if (event.button === 2 || (event.button === 0 && event.shiftKey)) {
        event.preventDefault();
        isDragging = true;
        lastDragY = event.clientY;
        
        container.style.cursor = 'grabbing';
        console.log('🤏 Starting vertical drag pan');
      }
    };
    
    const handleMouseMove = (event: MouseEvent) => {
      if (!isDragging || !chart) return;
      
      event.preventDefault();
      const currentY = event.clientY;
      const deltaY = currentY - lastDragY;
      const priceScale = chart.priceScale('right');
      
      // Calculate pan direction and apply incremental changes
      if (Math.abs(deltaY) > 1) { // Lower movement threshold for smoother response
        const panSensitivity = 0.8; // Increased sensitivity for better response
        
        // Accumulate the pan offset
        accumulatedPanY += deltaY * panSensitivity;
        
        // Convert accumulated pan to scale margins
        const panRange = Math.abs(accumulatedPanY) * 0.0001; // Scale factor
        const maxPan = 0.3; // Maximum pan range
        const clampedPan = Math.min(panRange, maxPan);
        
        if (accumulatedPanY > 0) {
          // Dragging down - show higher prices (pan up)
          priceScale.applyOptions({
            scaleMargins: {
              top: Math.max(0.01, 0.05 - clampedPan),
              bottom: Math.min(0.5, 0.05 + clampedPan)
            },
            autoScale: false
          });
        } else {
          // Dragging up - show lower prices (pan down)
          priceScale.applyOptions({
            scaleMargins: {
              top: Math.min(0.5, 0.05 + clampedPan),
              bottom: Math.max(0.01, 0.05 - clampedPan)
            },
            autoScale: false
          });
        }
        
        lastDragY = currentY;
      }
    };
    
    const handleMouseUp = () => {
      if (isDragging) {
        isDragging = false;
        container.style.cursor = 'default';
        
        // Don't reset accumulatedPanY - keep the pan position
        console.log('🤏 Finished vertical drag pan - position maintained', { totalPan: accumulatedPanY });
      }
    };
    
    // Add mouse event listeners for dragging
    container.addEventListener('mousedown', handleMouseDown);
    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mouseup', handleMouseUp);
    container.addEventListener('mouseleave', handleMouseUp); // Stop dragging if mouse leaves
    
    // Prevent context menu on right click during drag
    container.addEventListener('contextmenu', (event) => {
      if (isDragging) {
        event.preventDefault();
      }
    });
    
    // Add touch gesture support for trackpad-like interactions and vertical dragging
    let touchStartY = 0;
    let touchStartDistance = 0;
    let isMultiTouch = false;
    let isTouchDragging = false;
    let lastTouchY = 0;
    let accumulatedTouchPanY = 0; // Track touch pan offset
    
    const handleTouchStart = (event: TouchEvent) => {
      if (event.touches.length === 1) {
        touchStartY = event.touches[0].clientY;
        lastTouchY = event.touches[0].clientY;
        isMultiTouch = false;
        isTouchDragging = false;
      } else if (event.touches.length === 2) {
        // Two-finger gesture for pinch-to-zoom
        const touch1 = event.touches[0];
        const touch2 = event.touches[1];
        touchStartDistance = Math.sqrt(
          Math.pow(touch2.clientX - touch1.clientX, 2) + 
          Math.pow(touch2.clientY - touch1.clientY, 2)
        );
        isMultiTouch = true;
        isTouchDragging = false;
      }
    };
    
    const handleTouchMove = (event: TouchEvent) => {
      if (!chart) return;
      
      const priceScale = chart.priceScale('right');
      
      if (event.touches.length === 2 && isMultiTouch) {
        // Two-finger pinch gesture
        event.preventDefault();
        
        const touch1 = event.touches[0];
        const touch2 = event.touches[1];
        const currentDistance = Math.sqrt(
          Math.pow(touch2.clientX - touch1.clientX, 2) + 
          Math.pow(touch2.clientY - touch1.clientY, 2)
        );
        
        const distanceChange = currentDistance - touchStartDistance;
        const threshold = 10; // Minimum distance change to trigger zoom
        
        if (Math.abs(distanceChange) > threshold) {
          console.log('🤏 Touch pinch gesture detected');
          
          if (distanceChange > 0) {
            // Pinch out - zoom out
            priceScale.applyOptions({ 
              scaleMargins: { top: 0.01, bottom: 0.01 }
            });
          } else {
            // Pinch in - zoom in
            priceScale.applyOptions({ 
              scaleMargins: { top: 0.15, bottom: 0.15 }
            });
          }
          
          touchStartDistance = currentDistance;
          
          // Reset to auto-scale after gesture ends
          setTimeout(() => {
            priceScale.applyOptions({ autoScale: true });
          }, 200);
        }
      } else if (event.touches.length === 1 && !isMultiTouch) {
        // Single finger vertical drag for price panning
        const currentY = event.touches[0].clientY;
        const deltaY = currentY - lastTouchY;
        const threshold = 3; // Lower threshold for better response
        
        // Check for significant vertical movement
        if (Math.abs(deltaY) > threshold) {
          // Start dragging mode after initial movement
          if (!isTouchDragging && Math.abs(currentY - touchStartY) > 10) {
            isTouchDragging = true;
            console.log('👆 Touch vertical drag started');
          }
          
          if (isTouchDragging) {
            event.preventDefault();
            
            const panSensitivity = 0.5;
            
            // Accumulate the pan offset
            accumulatedTouchPanY += deltaY * panSensitivity;
            
            // Convert accumulated pan to scale margins
            const panRange = Math.abs(accumulatedTouchPanY) * 0.0001;
            const maxPan = 0.3;
            const clampedPan = Math.min(panRange, maxPan);
            
            if (accumulatedTouchPanY > 0) {
              // Dragging down - show higher prices (pan up)
              priceScale.applyOptions({
                scaleMargins: {
                  top: Math.max(0.01, 0.05 - clampedPan),
                  bottom: Math.min(0.5, 0.05 + clampedPan)
                },
                autoScale: false
              });
            } else {
              // Dragging up - show lower prices (pan down)
              priceScale.applyOptions({
                scaleMargins: {
                  top: Math.min(0.5, 0.05 + clampedPan),
                  bottom: Math.max(0.01, 0.05 - clampedPan)
                },
                autoScale: false
              });
            }
            
            lastTouchY = currentY;
          }
        }
      }
    };
    
    const handleTouchEnd = () => {
      if (isTouchDragging) {
        // Don't reset accumulatedTouchPanY - maintain the user's pan position
        console.log('👆 Touch vertical drag ended - position maintained', { totalTouchPan: accumulatedTouchPanY });
      }
      
      isMultiTouch = false;
      isTouchDragging = false;
    };
    
    // Add touch event listeners
    container.addEventListener('touchstart', handleTouchStart, { passive: false });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd);
    
    // Make container focusable for keyboard events
    container.setAttribute('tabindex', '0');
    container.style.outline = 'none'; // Remove focus outline
    
    console.log('✅ Enhanced scrolling controls set up successfully');

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        const container = chartContainerRef.current;
        chart.applyOptions({
          width: container.clientWidth,
          height: Math.max(500, Math.min(800, container.clientHeight || 600)),
        });
      }
    };

    // Use ResizeObserver for better resize handling
    let resizeObserver: ResizeObserver | null = null;
    if (window.ResizeObserver) {
      resizeObserver = new ResizeObserver(handleResize);
      resizeObserver.observe(chartContainerRef.current);
    } else {
      window.addEventListener('resize', handleResize);
    }

    return () => {
      // Clean up event listeners
      const container = chartContainerRef.current;
      if (container) {
        container.removeEventListener('keydown', handleKeyDown);
        container.removeEventListener('wheel', handleWheel);
        container.removeEventListener('mousedown', handleMouseDown);
        container.removeEventListener('mousemove', handleMouseMove);
        container.removeEventListener('mouseup', handleMouseUp);
        container.removeEventListener('mouseleave', handleMouseUp);
        container.removeEventListener('contextmenu', () => {});
        container.removeEventListener('touchstart', handleTouchStart);
        container.removeEventListener('touchmove', handleTouchMove);
        container.removeEventListener('touchend', handleTouchEnd);
      }
      
      // Clean up resize observer
      if (resizeObserver) {
        resizeObserver.disconnect();
      } else {
        window.removeEventListener('resize', handleResize);
      }
      
      // Clean up chart
      chart.remove();
      chartRef.current = null;
      candlestickSeriesRef.current = null;
      volumeSeriesRef.current = null;
      sentimentSeriesRef.current = null;
      
      console.log('🧹 Chart and event listeners cleaned up');
    };
  }, [forceUpdate]); // Create chart when component mounts or forceUpdate changes

  // Container readiness effect - ensures chart creation happens when container is ready
  useEffect(() => {
    console.log('📐 Container readiness check effect triggered');
    
    if (!chartContainerRef.current) {
      console.log('📐 Container not ready, waiting...');
      
      // More aggressive container ready check
      const checkContainer = () => {
        if (chartContainerRef.current && !chartRef.current) {
          console.log('📐 Container became ready! Dimensions:', {
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight
          });
          
          // Force re-render by updating a state that triggers chart creation
          setForceUpdate(prev => prev + 1); // This should trigger the chart creation useEffect
        }
      };
      
      // Check multiple times with shorter intervals
      const interval = setInterval(() => {
        if (chartContainerRef.current) {
          console.log('📐 Container ready via interval check');
          checkContainer();
          clearInterval(interval);
        }
      }, 50); // Check every 50ms instead of 100ms
      
      // Also check with requestAnimationFrame for better timing
      const rafCheck = () => {
        if (chartContainerRef.current && !chartRef.current) {
          checkContainer();
        } else if (!chartContainerRef.current) {
          requestAnimationFrame(rafCheck);
        }
      };
      requestAnimationFrame(rafCheck);
      
      // Clean up interval
      return () => clearInterval(interval);
    } else {
      console.log('📐 Container already ready');
      // If container is ready but chart isn't created, force creation
      if (!chartRef.current) {
        console.log('📐 Container ready but no chart, forcing creation...');
        setForceUpdate(prev => prev + 1);
      }
    }
  }, [forceUpdate]); // Include forceUpdate in dependencies

  // Update chart settings when timeframe changes
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.timeScale().applyOptions({
        secondsVisible: timeframe === '1H', // Show seconds only for hourly
      });
    }
  }, [timeframe]);

  // Effect for live data updates
  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || !sentimentSeriesRef.current) return;
    
    // Update live price data
    if (livePriceData) {
      const newTimestamp = ensureValidTimestamp(livePriceData.timestamp);
      
      // Only update if this is newer data
      if (newTimestamp > lastPriceTimestamp) {
        const candlestickPoint: CandlestickData = {
          time: newTimestamp as Time,
          open: livePriceData.open,
          high: livePriceData.high,
          low: livePriceData.low,
          close: livePriceData.close,
        };

        const volumePoint: HistogramData = {
          time: newTimestamp as Time,
          value: livePriceData.volume,
          color: livePriceData.close >= livePriceData.open ? CHART_COLORS.upCandle : CHART_COLORS.downCandle,
        };

        try {
          // Update chart with latest candle
          candlestickSeriesRef.current.update(candlestickPoint);
          volumeSeriesRef.current.update(volumePoint);
          setLastPriceTimestamp(newTimestamp);
          setLastUpdate(new Date(livePriceData.timestamp));
        } catch (error) {
          console.warn('Error updating price chart:', error, {
            newTimestamp,
            lastPriceTimestamp,
            timeComparison: newTimestamp > lastPriceTimestamp
          });
        }
      }
    }

    // Update live ML prediction
    if (liveMLPrediction) {
      const newMLTimestamp = ensureValidTimestamp(liveMLPrediction.timestamp);
      
      // Only update if this is newer ML data
      if (newMLTimestamp > lastMLTimestamp) {
        const sentimentPoint = {
          time: newMLTimestamp as Time,
          value: liveMLPrediction.sentimentScore,
        };

        try {
          sentimentSeriesRef.current.update(sentimentPoint);
          setLastMLTimestamp(newMLTimestamp);

          // Add marker for high confidence signals
          if (liveMLPrediction.confidence > 0.8 && liveMLPrediction.signal !== 'HOLD') {
            const marker = {
              time: newMLTimestamp as Time,
              position: liveMLPrediction.signal === 'BUY' ? 'belowBar' as const : 'aboveBar' as const,
              color: liveMLPrediction.signal === 'BUY' ? CHART_COLORS.buySignal : CHART_COLORS.sellSignal,
              shape: liveMLPrediction.signal === 'BUY' ? 'arrowUp' as const : 'arrowDown' as const,
              text: `${liveMLPrediction.signal} (${(liveMLPrediction.confidence * 100).toFixed(0)}%)`,
              size: 1,
            };

            // Get existing markers and add new one
            const existingMarkers = candlestickSeriesRef.current.markers?.() || [];
            candlestickSeriesRef.current.setMarkers([...existingMarkers, marker]);
          }
        } catch (error) {
          console.warn('Error updating ML prediction chart:', error);
        }
      }
    }
  }, [livePriceData, liveMLPrediction, lastPriceTimestamp, lastMLTimestamp]);

  // Reset timestamps when symbol changes
  useEffect(() => {
    setLastPriceTimestamp(0);
    setLastMLTimestamp(0);
  }, [symbol]);

  // Keyboard shortcuts for zoom
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle shortcuts when not typing in an input field
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (event.key) {
        case '+':
        case '=':
          event.preventDefault();
          handleZoomIn();
          break;
        case '-':
        case '_':
          event.preventDefault();
          handleZoomOut();
          break;
        case '0':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            handleResetZoom();
          }
          break;
        case 'f':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            handleFitToData();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Mouse wheel zoom (enhance default behavior)
  useEffect(() => {
    const chartContainer = chartContainerRef.current;
    if (!chartContainer) return;

    const handleWheel = () => {
      // Allow default TradingView zoom behavior
      // The chart already handles wheel events, this is just for custom enhancement if needed
    };

    chartContainer.addEventListener('wheel', handleWheel, { passive: true });
    return () => chartContainer.removeEventListener('wheel', handleWheel);
  }, []);

  // Helper function to create prediction markers (moved before useMemo)
  const createPredictionMarkers = useCallback((predictions: any[]) => {
    return predictions
      .filter(pred => pred.confidence > 0.6 && pred.signal && pred.signal !== 'HOLD') // Only show confident BUY/SELL signals
      .map(pred => {
        const signal = pred.signal;
        
        return {
          time: ensureValidTimestamp(pred.time) as Time,
          position: signal === 'BUY' ? 'belowBar' as const : 'aboveBar' as const,
          color: signal === 'BUY' ? CHART_COLORS.buySignal : CHART_COLORS.sellSignal,
          shape: signal === 'BUY' ? 'arrowUp' as const : 'arrowDown' as const,
          text: `${signal} (${pred.confidence.toFixed(2)})`,
          size: pred.confidence > 0.8 ? 2 : 1,
        };
      });
  }, []);

  // Memoized data transformations for better performance
  const transformedChartData = useMemo(() => {
    console.log('🔄 Transforming chart data:', { 
      chartData: chartData?.length, 
      hasData: !!chartData,
      sampleData: chartData?.slice(0, 2)
    });
    
    if (!chartData || chartData.length === 0) {
      console.log('❌ No chart data available');
      return null;
    }
    
    // Sort chart data by timestamp in ascending order
    const sortedChartData = [...chartData].sort((a, b) => a.timestamp - b.timestamp);
    
    // Transform OHLCV data to candlestick format
    const candlestickData = sortedChartData.map(item => ({
      time: ensureValidTimestamp(item.timestamp) as Time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    // Transform volume data
    const volumeData = sortedChartData.map(item => ({
      time: ensureValidTimestamp(item.timestamp) as Time,
      value: item.volume,
      color: item.close >= item.open ? '#00C851' : '#FF4444',
    }));

    console.log('✅ Chart data transformed:', { 
      candlestickCount: candlestickData.length,
      volumeCount: volumeData.length,
      firstCandle: candlestickData[0],
      lastCandle: candlestickData[candlestickData.length - 1]
    });

    return { candlestickData, volumeData, sortedChartData };
  }, [chartData]);

  const transformedMLData = useMemo(() => {
    console.log('🔄 Transforming ML data:', { 
      mlPredictions: mlPredictions?.length, 
      hasData: !!mlPredictions,
      sampleData: mlPredictions?.slice(0, 2)
    });
    
    if (!mlPredictions || mlPredictions.length === 0) {
      console.log('❌ No ML predictions available');
      return null;
    }

    // Sort data by time in ascending order (TradingView requirement)
    const sortedPredictions = [...mlPredictions].sort((a, b) => a.time - b.time);
    
    const sentimentData = sortedPredictions.map(pred => ({
      time: ensureValidTimestamp(pred.time) as Time,
      value: pred.sentimentScore,
    }));

    const markers = createPredictionMarkers(sortedPredictions);

    console.log('✅ ML data transformed:', { 
      sentimentCount: sentimentData.length,
      markersCount: markers.length,
      firstSentiment: sentimentData[0],
      lastSentiment: sentimentData[sentimentData.length - 1]
    });

    return { sentimentData, markers, sortedPredictions };
  }, [mlPredictions, createPredictionMarkers]);

  const loadChartData = useCallback(() => {
    console.log('📊 Loading chart data...', {
      hasChartRef: !!chartRef.current,
      hasCandlestickSeries: !!candlestickSeriesRef.current,
      hasVolumeSeries: !!volumeSeriesRef.current,
      hasSentimentSeries: !!sentimentSeriesRef.current,
      hasTransformedChartData: !!transformedChartData,
      hasTransformedMLData: !!transformedMLData
    });
    
    if (!candlestickSeriesRef.current || !sentimentSeriesRef.current || !volumeSeriesRef.current) {
      console.log('❌ Chart series not ready');
      return;
    }

    setIsLoading(true);

    try {
      // Use transformed data if available, otherwise generate sample data
      if (transformedChartData) {
        console.log('📈 Setting real chart data...');
        candlestickSeriesRef.current.setData(transformedChartData.candlestickData);
        volumeSeriesRef.current.setData(transformedChartData.volumeData);
        
        // Set the last timestamp to the most recent data point
        if (transformedChartData.sortedChartData.length > 0) {
          const lastDataPoint = transformedChartData.sortedChartData[transformedChartData.sortedChartData.length - 1];
          setLastPriceTimestamp(ensureValidTimestamp(lastDataPoint.timestamp));
        }
        
        setLastUpdate(new Date());
      } else {
        console.log('📊 Generating sample chart data...');
        // Generate sample candlestick data
        const sampleCandlestickData = generateSampleCandlestickData();
        const sampleVolumeData = generateSampleVolumeData();
        candlestickSeriesRef.current.setData(sampleCandlestickData);
        volumeSeriesRef.current.setData(sampleVolumeData);
        console.log('📊 Sample data set:', { candleCount: sampleCandlestickData.length, volumeCount: sampleVolumeData.length });
      }

      // Load ML sentiment data
      if (transformedMLData) {
        console.log('🤖 Setting real ML data...');
        sentimentSeriesRef.current.setData(transformedMLData.sentimentData);
        
        // Set the last ML timestamp to the most recent prediction
        if (transformedMLData.sortedPredictions.length > 0) {
          const lastPrediction = transformedMLData.sortedPredictions[transformedMLData.sortedPredictions.length - 1];
          setLastMLTimestamp(ensureValidTimestamp(lastPrediction.time));
        }

        // Add prediction markers for high confidence signals
        candlestickSeriesRef.current.setMarkers(transformedMLData.markers);
      } else {
        console.log('🤖 Generating sample ML data...');
        // Generate sample sentiment data
        const sampleSentimentData = generateSampleSentimentData();
        sentimentSeriesRef.current.setData(sampleSentimentData);
        
        // Add sample markers
        const sampleMarkers = generateSampleMarkers();
        candlestickSeriesRef.current.setMarkers(sampleMarkers);
        console.log('🤖 Sample ML data set:', { sentimentCount: sampleSentimentData.length, markersCount: sampleMarkers.length });
      }

      console.log('✅ Chart data loading completed');

    } catch (error) {
      console.error('❌ Error loading chart data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [transformedChartData, transformedMLData]);

  // Load data when chart is ready or data changes
  useEffect(() => {
    console.log('🔄 useEffect triggered:', {
      hasChartRef: !!chartRef.current,
      hasCandlestick: !!candlestickSeriesRef.current,
      hasVolume: !!volumeSeriesRef.current,
      hasSentiment: !!sentimentSeriesRef.current,
      chartLoading,
      mlLoading,
      hasTransformedChartData: !!transformedChartData,
      hasTransformedMLData: !!transformedMLData
    });
    
    // Force load sample data if chart is ready but no data after 2 seconds
    if (chartRef.current && candlestickSeriesRef.current && volumeSeriesRef.current && sentimentSeriesRef.current) {
      console.log('✅ Chart series ready, forcing sample data load...');
      setTimeout(() => {
        try {
          const sampleCandlestickData = generateSampleCandlestickData();
          const sampleVolumeData = generateSampleVolumeData();
          const sampleSentimentData = generateSampleSentimentData();
          const sampleMarkers = generateSampleMarkers();
          
          console.log('🚨 Loading sample data as primary option...');
          candlestickSeriesRef.current?.setData(sampleCandlestickData);
          volumeSeriesRef.current?.setData(sampleVolumeData);
          sentimentSeriesRef.current?.setData(sampleSentimentData);
          candlestickSeriesRef.current?.setMarkers(sampleMarkers);
          
          console.log('✅ Sample data loaded successfully');
          setIsLoading(false);
        } catch (error) {
          console.error('❌ Error loading sample data:', error);
        }
      }, 500); // Load sample data quickly
    }
    
    // Also try to load real data if available
    if (chartRef.current && candlestickSeriesRef.current && volumeSeriesRef.current && sentimentSeriesRef.current && !chartLoading && !mlLoading) {
      console.log('✅ All conditions met, attempting to load real data...');
      loadChartData();
    } else {
      console.log('⏳ Waiting for conditions to be met...');
    }
    
    // Sync isLoading state with hook loading states
    setIsLoading(chartLoading || mlLoading);
  }, [transformedChartData, transformedMLData, chartLoading, mlLoading, loadChartData]);

  const generateSampleCandlestickData = () => {
    const config = TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG] || TIMEFRAME_CONFIG['1D'];
    const data = [];
    const now = new Date();
    let lastClose = 118; // Starting price for CBA
    
    for (let i = 0; i < config.dataPoints; i++) {
      const time = new Date(now.getTime() - (config.dataPoints - 1 - i) * config.interval * 1000);
      const timestamp = Math.floor(time.getTime() / 1000) as Time;
      
      // Generate realistic OHLC data
      const volatility = 0.02; // 2% volatility
      const change = (Math.random() - 0.5) * volatility * lastClose;
      const open = lastClose;
      const close = Math.max(open + change, 110); // Minimum price floor
      
      // High and low based on open/close
      const maxPrice = Math.max(open, close);
      const minPrice = Math.min(open, close);
      const high = maxPrice + Math.random() * volatility * 0.5 * maxPrice;
      const low = minPrice - Math.random() * volatility * 0.5 * minPrice;
      
      data.push({
        time: timestamp,
        open,
        high,
        low,
        close,
      });
      
      lastClose = close;
    }
    
    return data;
  };

  const generateSampleVolumeData = () => {
    const config = TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG] || TIMEFRAME_CONFIG['1D'];
    const data = [];
    const now = new Date();
    
    for (let i = 0; i < config.dataPoints; i++) {
      const time = new Date(now.getTime() - (config.dataPoints - 1 - i) * config.interval * 1000);
      const timestamp = Math.floor(time.getTime() / 1000) as Time;
      
      // Generate realistic volume (millions of shares)
      const baseVolume = 5000000; // 5M shares base
      const volume = baseVolume + Math.random() * baseVolume * 2;
      
      data.push({
        time: timestamp,
        value: volume,
        color: Math.random() > 0.5 ? '#00C851' : '#FF4444',
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



  // Skeleton Loader Component
  const ChartSkeleton = () => (
    <div className="w-full">
      <div className="mb-4 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-48 mb-2"></div>
        <div className="h-4 bg-gray-800 rounded w-64"></div>
      </div>
      <div className="h-96 bg-gray-800 rounded-lg animate-pulse flex items-center justify-center">
        <div className="text-gray-500 flex items-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
          <span>Loading chart data...</span>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-800 rounded animate-pulse"></div>
        ))}
      </div>
    </div>
  );

  // Error Display Component
  const ChartError = ({ error, onRetry }: { error: string; onRetry: () => void }) => (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white mb-2">
          {symbol} - Chart Error
        </h3>
      </div>
      <div className="h-96 bg-gray-900 rounded-lg border border-red-500/50 flex items-center justify-center">
        <div className="text-center p-6">
          <div className="text-red-400 text-4xl mb-4">📊</div>
          <h4 className="text-red-400 text-lg mb-2">Chart Data Error</h4>
          <p className="text-gray-300 mb-4 max-w-md">
            {error}
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              Retry Loading
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Handle loading states
  if (chartLoading || mlLoading) {
    return <ChartSkeleton />;
  }

  // Handle error states
  if (chartError || mlError) {
    const errorMessage = chartError || mlError || 'Unknown error occurred';
    return (
      <ChartError
        error={errorMessage}
        onRetry={() => {
          // Force re-fetch by changing the key or calling refresh
          window.location.reload();
        }}
      />
    );
  }

  return (
    <div className="w-full overflow-auto transition-all duration-300" style={{ maxHeight: '100vh' }}>
      {/* Chart Header - Responsive */}
      <div className="mb-4 flex flex-col lg:flex-row lg:justify-between lg:items-start space-y-2 lg:space-y-0">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg lg:text-xl font-semibold text-white truncate">
            {symbol} - {TIMEFRAME_CONFIG[timeframe as keyof typeof TIMEFRAME_CONFIG]?.label || timeframe}
          </h3>
          <div className="flex flex-wrap items-center gap-1 lg:gap-2 text-xs lg:text-sm text-gray-400">
            <span className="hidden sm:inline">Price Chart with ML Sentiment Analysis</span>
            <span className="hidden sm:inline">•</span>
            <span className="text-blue-400">{getMarketStatus()}</span>
            <span>•</span>
            <span className="hidden md:inline">{getCurrentAustralianTime()}</span>
            <span className="md:hidden">{getCurrentAustralianTime().split(' ')[1]}</span>
            <span>•</span>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-1 transition-all duration-300 ${isConnected && isLive ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className={`transition-colors duration-300 ${isConnected && isLive ? 'text-green-400' : 'text-red-400'}`}>
                {isConnected && isLive ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>
            {lastUpdate && (
              <>
                <span className="hidden lg:inline">•</span>
                <span className="hidden lg:inline text-xs">Updated: {lastUpdate.toLocaleTimeString('en-AU', { 
                  timeZone: 'Australia/Sydney',
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                })}</span>
              </>
            )}
          </div>
        </div>
        
        {/* Legend and Controls - Responsive */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-2 lg:gap-4">
          {/* Legend */}
          <div className="flex flex-wrap gap-2 lg:gap-3 text-xs lg:text-sm">
            <div className="flex items-center">
              <div className="w-2 h-2 lg:w-3 lg:h-3 bg-blue-500 rounded mr-1 lg:mr-2 animate-pulse"></div>
              <span className="text-gray-300">Price</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 lg:w-3 lg:h-3 bg-green-500 rounded mr-1 lg:mr-2"></div>
              <span className="text-gray-300">ML</span>
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 lg:w-3 lg:h-3 bg-yellow-500 rounded mr-1 lg:mr-2"></div>
              <span className="text-gray-300">Signals</span>
            </div>
          </div>
          
          {/* Zoom Controls - More compact on mobile */}
          <div className="flex items-center gap-1">
            <span className="text-gray-400 text-xs hidden sm:inline">Zoom:</span>
            <button
              onClick={handleZoomIn}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs transition-all duration-200 hover:scale-105"
              title="Zoom In (+ key)"
            >
              +
            </button>
            <button
              onClick={handleZoomOut}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs transition-all duration-200 hover:scale-105"
              title="Zoom Out (- key)"
            >
              −
            </button>
            <button
              onClick={handleResetZoom}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs transition-all duration-200 hover:scale-105"
              title="Reset Zoom (Ctrl+0)"
            >
              ⌂
            </button>
            <button
              onClick={handleFitToData}
              className="px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs transition-all duration-200 hover:scale-105"
              title="Fit to Data (Ctrl+F)"
            >
              ⟷
            </button>
            <div className="text-xs text-gray-500 ml-1 hidden lg:block" title="Use mouse wheel to zoom, drag to pan">
              💡
            </div>
          </div>
        </div>
      </div>

      {/* Loading indicator - Responsive positioning */}
      {isLoading && (
        <div className="fixed top-4 right-4 lg:absolute lg:top-2 lg:right-2 bg-blue-600 text-white px-2 lg:px-3 py-1 rounded text-xs lg:text-sm z-10 animate-pulse">
          <div className="flex items-center space-x-1">
            <div className="animate-spin rounded-full h-3 w-3 border-b border-white"></div>
            <span className="hidden sm:inline">Loading {timeframe} data...</span>
            <span className="sm:hidden">Loading...</span>
          </div>
        </div>
      )}
      
      {/* Chart Container with improved scrolling */}
      <div 
        ref={chartContainerRef}
        className="chart-container w-full rounded-lg border-2 border-blue-500"
        style={{ 
          backgroundColor: '#1a1a1a', // Make sure background is visible
          height: '70vh',  // Use viewport height instead of calc
          minHeight: '500px',  // Maintain minimum height
          maxHeight: '800px',  // Prevent excessive height
          position: 'relative',
          touchAction: 'pan-x pan-y',  // Allow both horizontal and vertical panning
          overflow: 'hidden',  // Let TradingView handle its own scrolling
        }}
      >
        {/* Debug overlay */}
        <div className="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 text-xs z-50">
          Chart Container: {chartContainerRef.current?.clientWidth}x{chartContainerRef.current?.clientHeight}
          {chartRef.current ? ' ✅ Chart Created' : ' ❌ No Chart'}
        </div>
        
     
        
        {/* Force Chart Creation Button for Debugging */}
        {!chartRef.current && (
          <div className="absolute top-12 left-2 z-50">
            <button 
              onClick={() => {
                console.log('🔧 Force chart creation clicked');
                if (!chartContainerRef.current) {
                  console.log('❌ No container available');
                  return;
                }
                
                try {
                  console.log('🔧 Attempting to create chart manually...');
                  const chart = createChart(chartContainerRef.current, {
                    layout: { background: { color: '#1a1a1a' }, textColor: '#d1d4dc' },
                    width: chartContainerRef.current.clientWidth,
                    height: 500,
                  });
                  
                  chartRef.current = chart;
                  
                  const candlestickSeries = chart.addCandlestickSeries({
                    upColor: '#00C851',
                    downColor: '#FF4444',
                    borderUpColor: '#00C851',
                    borderDownColor: '#FF4444',
                    wickUpColor: '#00C851',
                    wickDownColor: '#FF4444',
                  });
                  
                  candlestickSeriesRef.current = candlestickSeries;
                  
                  // Add simple test data
                  const testData = [
                    { time: '2024-01-01', open: 100, high: 110, low: 95, close: 105 },
                    { time: '2024-01-02', open: 105, high: 115, low: 100, close: 108 },
                    { time: '2024-01-03', open: 108, high: 120, low: 105, close: 115 },
                  ];
                  
                  candlestickSeries.setData(testData);
                  console.log('✅ Manual chart creation successful!');
                } catch (error) {
                  console.error('❌ Manual chart creation failed:', error);
                }
              }}
              className="bg-yellow-500 text-black px-2 py-1 text-xs rounded"
            >
              Force Create Chart
            </button>
          </div>
        )}
      </div>
      
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
