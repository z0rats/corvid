import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('NewsfeedIocParser');

export function parseIOCs(iocData) {
  if (!iocData) return {};

  try {
    if (typeof iocData === 'string') {
      return JSON.parse(iocData);
    }
    return iocData;
  } catch (error) {
    logger.error('Failed to parse IOCs:', error);
    return {};
  }
}

export function parseAnalysisResult(analysisResult) {
  if (!analysisResult) return null;

  try {
    if (typeof analysisResult === 'string') {
      return JSON.parse(analysisResult);
    }
    return analysisResult;
  } catch (error) {
    logger.error('Failed to parse analysis result:', error);
    return null;
  }
}
