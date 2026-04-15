import api from '../../../core/services/baseApi';

export function getFeedIconUrl(icon) {
  const iconFile = icon.endsWith('.png') ? icon : `${icon}.png`;
  return `${api.defaults.baseURL}/api/feedicons/${iconFile}`;
}

export function getStreamUrl() {
  return `${api.defaults.baseURL}/api/newsfeed/analysis/top-articles/stream`;
}
