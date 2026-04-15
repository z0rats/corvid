import { TYPE_COLOR_MAP } from '../constants/defangerConstants';

export const getTypeColor = (type) => TYPE_COLOR_MAP[type] || 'default';

export const createFallbackResults = (inputText) =>
  inputText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((originalIOC) => ({
      original: originalIOC,
      processed: originalIOC,
      types: ['Unknown'],
      changed: false,
    }));
