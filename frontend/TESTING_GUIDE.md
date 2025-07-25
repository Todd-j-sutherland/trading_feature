# Frontend Testing Setup Guide

## Test Dependencies Installation

To run comprehensive tests for the React frontend, install these dependencies:

```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install --save-dev jest @types/jest jest-environment-jsdom
npm install --save-dev @babel/preset-env @babel/preset-react @babel/preset-typescript
```

## Test Configuration

### jest.config.js
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

### setupTests.ts
```typescript
import '@testing-library/jest-dom';

// Mock lightweight-charts
jest.mock('lightweight-charts', () => ({
  createChart: jest.fn(() => ({
    addCandlestickSeries: jest.fn(() => ({
      setData: jest.fn(),
      setMarkers: jest.fn(),
      update: jest.fn(),
    })),
    addHistogramSeries: jest.fn(() => ({
      setData: jest.fn(),
      update: jest.fn(),
    })),
    addLineSeries: jest.fn(() => ({
      setData: jest.fn(),
      update: jest.fn(),
    })),
    remove: jest.fn(),
    applyOptions: jest.fn(),
  })),
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
}));
```

## Test Scenarios Covered

### 1. Chart Stability Tests
- ✅ Chart instance creation only once
- ✅ Proper cleanup on unmount
- ✅ Memory leak prevention
- ✅ Data transformation memoization

### 2. Error Handling Tests
- ✅ API error boundaries
- ✅ Network disconnection handling
- ✅ Race condition prevention
- ✅ Request cancellation

### 3. Performance Tests
- ✅ Component memoization
- ✅ Callback optimization
- ✅ Data processing efficiency
- ✅ Responsive design validation

### 4. User Interaction Tests
- ✅ Zoom controls functionality
- ✅ Keyboard shortcuts
- ✅ Touch gesture support (mobile)
- ✅ Accessibility compliance

## Running Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test TradingChart.test.tsx

# Run tests in watch mode
npm test -- --watch
```

## Performance Benchmarks

### Chart Rendering Performance
- Initial load: < 500ms
- Data update: < 100ms
- Zoom/pan operations: < 50ms
- Memory usage: < 50MB

### Network Request Optimization
- Request cancellation: ✅ Implemented
- Exponential backoff: ✅ Implemented
- Race condition handling: ✅ Implemented
- Offline detection: ✅ Implemented

## Visual Regression Testing

For visual regression testing, consider adding:

```bash
npm install --save-dev @storybook/react @storybook/test-runner
npm install --save-dev chromatic
```

This will enable:
- Component story testing
- Visual diff detection
- Cross-browser compatibility testing
- Responsive design validation

## End-to-End Testing

For E2E testing with real API interactions:

```bash
npm install --save-dev @playwright/test
```

Create tests for:
- Full user workflows
- Real-time data updates
- Error recovery scenarios
- Performance under load
