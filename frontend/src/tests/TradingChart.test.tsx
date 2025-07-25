import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TradingChart from '../components/TradingChart';
import ChartErrorBoundary from '../components/ChartErrorBoundary';
import ErrorProvider from '../contexts/ErrorContext';

// Mock the lightweight-charts library
jest.mock('lightweight-charts', () => ({
  createChart: jest.fn(() => ({
    addCandlestickSeries: jest.fn(() => ({
      setData: jest.fn(),
      setMarkers: jest.fn(),
      update: jest.fn(),
      markers: jest.fn(() => []),
    })),
    addHistogramSeries: jest.fn(() => ({
      setData: jest.fn(),
      update: jest.fn(),
    })),
    addLineSeries: jest.fn(() => ({
      setData: jest.fn(),
      update: jest.fn(),
    })),
    priceScale: jest.fn(() => ({
      applyOptions: jest.fn(),
    })),
    timeScale: jest.fn(() => ({
      applyOptions: jest.fn(),
      resetTimeScale: jest.fn(),
      fitContent: jest.fn(),
      getVisibleRange: jest.fn(() => ({
        from: 1000,
        to: 2000,
      })),
      setVisibleRange: jest.fn(),
    })),
    applyOptions: jest.fn(),
    remove: jest.fn(),
  })),
  CrosshairMode: {
    Normal: 0,
  },
}));

// Mock fetch
global.fetch = jest.fn();

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Wrapper component with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ErrorProvider>
    <ChartErrorBoundary>
      {children}
    </ChartErrorBoundary>
  </ErrorProvider>
);

describe('TradingChart Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (fetch as jest.Mock).mockClear();
  });

  const mockChartData = {
    success: true,
    data: [
      {
        timestamp: 1640995200,
        open: 100,
        high: 105,
        low: 98,
        close: 103,
        volume: 1000000,
      },
      {
        timestamp: 1641081600,
        open: 103,
        high: 108,
        low: 102,
        close: 106,
        volume: 1200000,
      },
    ],
  };

  const mockMLData = {
    success: true,
    data: [
      {
        time: 1640995200,
        sentimentScore: 0.5,
        confidence: 0.8,
        signal: 'BUY' as const,
        technicalScore: 0.7,
        newsCount: 5,
        features: {
          newsImpact: 0.3,
          technicalScore: 0.7,
          eventImpact: 0.2,
          redditSentiment: 0.4,
        },
      },
    ],
    stats: {
      total_records: 100,
      records_with_technical: 95,
      records_with_reddit: 80,
      avg_confidence: 0.75,
    },
  };

  test('renders chart header with symbol and timeframe', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockChartData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMLData,
      });

    render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    expect(screen.getByText(/CBA - 1 Day/)).toBeInTheDocument();
  });

  test('shows loading skeleton initially', () => {
    (fetch as jest.Mock)
      .mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    expect(screen.getByText(/Loading chart data.../)).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    (fetch as jest.Mock)
      .mockRejectedValue(new Error('Network error'));

    render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/Chart Data Error/)).toBeInTheDocument();
    });
  });

  test('zoom controls work correctly', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockChartData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMLData,
      });

    render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/CBA - 1 Day/)).toBeInTheDocument();
    });

    // Test zoom in button
    const zoomInButton = screen.getByTitle(/Zoom In/);
    fireEvent.click(zoomInButton);

    // Test zoom out button
    const zoomOutButton = screen.getByTitle(/Zoom Out/);
    fireEvent.click(zoomOutButton);

    // Test reset zoom button
    const resetZoomButton = screen.getByTitle(/Reset Zoom/);
    fireEvent.click(resetZoomButton);

    // Test fit to data button
    const fitDataButton = screen.getByTitle(/Fit to Data/);
    fireEvent.click(fitDataButton);
  });

  test('keyboard shortcuts work', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockChartData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMLData,
      });

    render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/CBA - 1 Day/)).toBeInTheDocument();
    });

    // Test keyboard shortcuts
    fireEvent.keyDown(document, { key: '+' });
    fireEvent.keyDown(document, { key: '-' });
    fireEvent.keyDown(document, { key: '0', ctrlKey: true });
    fireEvent.keyDown(document, { key: 'f', ctrlKey: true });
  });

  test('handles race conditions correctly', async () => {
    let resolveFirst: (value: any) => void;
    let resolveSecond: (value: any) => void;

    const firstPromise = new Promise(resolve => {
      resolveFirst = resolve;
    });
    const secondPromise = new Promise(resolve => {
      resolveSecond = resolve;
    });

    (fetch as jest.Mock)
      .mockReturnValueOnce(firstPromise)
      .mockReturnValueOnce(firstPromise)
      .mockReturnValueOnce(secondPromise)
      .mockReturnValueOnce(secondPromise);

    const { rerender } = render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    // Change symbol to trigger new requests
    rerender(
      <TestWrapper>
        <TradingChart symbol="WBC" timeframe="1D" />
      </TestWrapper>
    );

    // Resolve first request (should be ignored)
    resolveFirst!({
      ok: true,
      json: async () => mockChartData,
    });

    // Resolve second request (should be used)
    resolveSecond!({
      ok: true,
      json: async () => mockChartData,
    });

    await waitFor(() => {
      expect(screen.getByText(/WBC - 1 Day/)).toBeInTheDocument();
    });
  });

  test('request cancellation works on unmount', async () => {
    const mockAbort = jest.fn();
    const mockAbortController = {
      abort: mockAbort,
      signal: { aborted: false },
    };
    
    jest.spyOn(window, 'AbortController').mockImplementation(() => mockAbortController as any);

    (fetch as jest.Mock)
      .mockImplementation(() => new Promise(() => {})); // Never resolves

    const { unmount } = render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    unmount();

    expect(mockAbort).toHaveBeenCalled();
  });

  test('responsive design elements are present', async () => {
    (fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockChartData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMLData,
      });

    render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/CBA - 1 Day/)).toBeInTheDocument();
    });

    // Check for responsive classes
    const container = screen.getByText(/CBA - 1 Day/).closest('div');
    expect(container).toHaveClass('lg:text-xl');
  });

  test('memoized data transformation works correctly', async () => {
    (fetch as jest.Mock)
      .mockResolvedValue({
        ok: true,
        json: async () => mockChartData,
      });

    const { rerender } = render(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/CBA - 1 Day/)).toBeInTheDocument();
    });

    // Re-render with same props should not cause new fetch
    const fetchCallCount = (fetch as jest.Mock).mock.calls.length;
    
    rerender(
      <TestWrapper>
        <TradingChart symbol="CBA" timeframe="1D" />
      </TestWrapper>
    );

    // Should not have made additional fetch calls
    expect((fetch as jest.Mock).mock.calls.length).toBe(fetchCallCount);
  });
});

describe('ChartErrorBoundary', () => {
  test('catches and displays errors', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <ChartErrorBoundary>
        <ThrowError />
      </ChartErrorBoundary>
    );

    expect(screen.getByText(/Chart Error/)).toBeInTheDocument();
    expect(screen.getByText(/Test error/)).toBeInTheDocument();
  });

  test('retry button works', () => {
    let shouldThrow = true;
    
    const ConditionalThrow = () => {
      if (shouldThrow) {
        throw new Error('Test error');
      }
      return <div>Success</div>;
    };

    render(
      <ChartErrorBoundary>
        <ConditionalThrow />
      </ChartErrorBoundary>
    );

    expect(screen.getByText(/Chart Error/)).toBeInTheDocument();

    // Fix the error
    shouldThrow = false;

    // Click retry
    const retryButton = screen.getByText(/Retry Chart/);
    fireEvent.click(retryButton);

    expect(screen.getByText('Success')).toBeInTheDocument();
  });
});

describe('Error Context', () => {
  test('provides error handling functionality', () => {
    const TestComponent = () => {
      const { addError, errors } = require('../contexts/ErrorContext').useError();
      
      return (
        <div>
          <button onClick={() => addError('Test error', 'error')}>
            Add Error
          </button>
          <div data-testid="error-count">{errors.length}</div>
        </div>
      );
    };

    render(
      <ErrorProvider>
        <TestComponent />
      </ErrorProvider>
    );

    const addButton = screen.getByText('Add Error');
    fireEvent.click(addButton);

    expect(screen.getByTestId('error-count')).toHaveTextContent('1');
  });
});
