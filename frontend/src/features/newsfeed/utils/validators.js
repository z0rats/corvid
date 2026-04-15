import { SETTINGS } from '../constants/newsfeedConstants';

export function validateRetentionDays(days) {
  const numDays = parseInt(days);
  
  if (isNaN(numDays) || numDays < SETTINGS.MIN_RETENTION_DAYS) {
    return {
      isValid: false,
      error: `Retention period must be at least ${SETTINGS.MIN_RETENTION_DAYS} day`
    };
  }
  
  return { isValid: true };
}

export function validateFetchInterval(minutes) {
  const numMinutes = parseInt(minutes);
  
  if (isNaN(numMinutes) || numMinutes < SETTINGS.MIN_FETCH_INTERVAL) {
    return {
      isValid: false,
      error: `Fetch interval must be at least ${SETTINGS.MIN_FETCH_INTERVAL} minutes`
    };
  }
  
  return { isValid: true };
}

export function validateDateRange(startDate, endDate) {
  if (!startDate || !endDate) {
    return { isValid: true }; // Empty dates are allowed
  }
  
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return {
      isValid: false,
      error: 'Invalid date format'
    };
  }
  
  if (start > end) {
    return {
      isValid: false,
      error: 'Start date must be before end date'
    };
  }
  
  return { isValid: true };
}

export function validateFilters(filters) {
  const errors = {};
  
  // Validate date range
  const dateValidation = validateDateRange(filters.start_date, filters.end_date);
  if (!dateValidation.isValid) {
    errors.dateRange = dateValidation.error;
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}
