import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('NewsfeedFormatters');

export function formatDate(dateString) {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    logger.error('Error formatting date:', error);
    return dateString;
  }
}

export function formatTimeRange(timeRange) {
  const ranges = {
    '1d': '1 day',
    '7d': '7 days',
    '30d': '30 days',
    '90d': '90 days',
  };
  
  return ranges[timeRange] || timeRange;
}

export function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

export function truncateText(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}
