import { trendsApi } from '../../services/api/trendsApi';
import { useTrendsFetch } from './useTrendsFetch';

export function useWordFrequency(timeRange, refreshKey) {
  return useTrendsFetch(trendsApi.getTitleWordFrequency, [10, timeRange], [refreshKey, timeRange]);
}

export function useTopIocs(iocType, timeRange, refreshKey) {
  return useTrendsFetch(trendsApi.getTopIocs, [iocType, 10, timeRange], [iocType, refreshKey, timeRange]);
}

export function useTopCves(timeRange, refreshKey) {
  return useTrendsFetch(trendsApi.getTopCves, [10, timeRange], [refreshKey, timeRange]);
}

export function useIocDistribution(timeRange, refreshKey) {
  return useTrendsFetch(trendsApi.getIocTypeDistribution, [timeRange], [refreshKey, timeRange]);
}
