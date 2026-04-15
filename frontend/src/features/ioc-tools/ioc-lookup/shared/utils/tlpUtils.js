import { modeValue } from '../../../../../core/utils/themeUtils';

export const TLP_COLORS = {
    RED: '#d32f2f',
    AMBER: '#ffa000',
    GREEN: '#388e3c',
    BLUE: '#1976d2',
    WHITE: '#bdbdbd',
    NONE: 'transparent',
  };

  export const TLP_HIERARCHY = ['RED', 'AMBER', 'GREEN', 'BLUE', 'WHITE'];

  /**
   * Determines the overall TLP level from a list of TLP values based on hierarchy.
   * @param {string[]} serviceTlps - An array of TLP strings (e.g., ['GREEN', 'RED']).
   * @returns {string} The highest priority TLP found, or 'WHITE' as a default.
   */
  export const getOverallTlp = (serviceTlps) => {
    if (!serviceTlps || serviceTlps.length === 0) {
      return 'WHITE';
    }
    for (const tlp of TLP_HIERARCHY) {
      if (serviceTlps.includes(tlp)) {
        return tlp;
      }
    }
    return 'WHITE';
  };

  export const getTlpBackgroundColor = (tlpValue, status, theme) => {
    if (status === 'loading') return 'transparent';
    if (status === 'error') {
      return modeValue(theme, theme.palette.grey[800], theme.palette.action.disabledBackground);
    }
    if (tlpValue === 'WHITE' || tlpValue === 'NONE') return 'transparent';
    return TLP_COLORS[tlpValue] || 'transparent';
  };