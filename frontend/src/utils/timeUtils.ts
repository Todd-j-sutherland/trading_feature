/**
 * Time utilities for Australian Eastern Time display
 */

// Australian Eastern Time timezone
const AUSTRALIA_TZ = 'Australia/Sydney';

/**
 * Format Unix timestamp to Australian Eastern Time string
 */
export const formatAustralianTime = (timestamp: number, options?: Intl.DateTimeFormatOptions): string => {
  const date = new Date(timestamp * 1000); // Convert from Unix timestamp
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: AUSTRALIA_TZ,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false, // 24-hour format for trading
    ...options,
  };

  return date.toLocaleString('en-AU', defaultOptions);
};

/**
 * Format timestamp for chart tooltips
 */
export const formatChartTime = (timestamp: number, timeframe: string): string => {
  const options: Intl.DateTimeFormatOptions = {
    timeZone: AUSTRALIA_TZ,
  };

  switch (timeframe) {
    case '1H':
      options.month = 'short';
      options.day = 'numeric';
      options.hour = '2-digit';
      options.minute = '2-digit';
      break;
    case '1D':
      options.month = 'short';
      options.day = 'numeric';
      options.year = 'numeric';
      break;
    case '1W':
      options.month = 'short';
      options.day = 'numeric';
      options.year = 'numeric';
      break;
    case '1M':
      options.month = 'long';
      options.year = 'numeric';
      break;
    default:
      options.month = 'short';
      options.day = 'numeric';
      options.hour = '2-digit';
      options.minute = '2-digit';
  }

  return formatAustralianTime(timestamp, options);
};

/**
 * Get current Australian Eastern Time
 */
export const getCurrentAustralianTime = (): string => {
  return new Date().toLocaleString('en-AU', {
    timeZone: AUSTRALIA_TZ,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
};

/**
 * Check if current time is during ASX trading hours
 */
export const isMarketHours = (): boolean => {
  const now = new Date();
  const aestTime = new Date(now.toLocaleString('en-US', { timeZone: AUSTRALIA_TZ }));
  const hours = aestTime.getHours();
  const minutes = aestTime.getMinutes();
  const day = aestTime.getDay(); // 0 = Sunday, 6 = Saturday
  
  // ASX trading hours: Monday-Friday, 10:00 AM - 4:00 PM AEST
  const isWeekday = day >= 1 && day <= 5;
  const isAfterOpen = hours > 10 || (hours === 10 && minutes >= 0);
  const isBeforeClose = hours < 16;
  
  return isWeekday && isAfterOpen && isBeforeClose;
};

/**
 * Get market status string
 */
export const getMarketStatus = (): string => {
  if (isMarketHours()) {
    return 'Market Open (AEST)';
  } else {
    return 'Market Closed (AEST)';
  }
};
