export const SIGMA_CONSTANTS = {
  STATUSES: ['None', 'Experimental', 'Test', 'Stable', 'Deprecated', 'Unsupported'],
  LEVELS: ['None', 'Informational', 'Low', 'Medium', 'High', 'Critical'],
  MODIFIERS: [
    'equals',
    'contains',
    'startswith',
    'endswith',
    'all',
    'base64',
    'base64offset',
    'utf16',
    'utf16le',
    'utf16be',
    'wide',
    're'
  ],
  CONDITIONS: [
    'all',
    'any',
    '1 of them',
    'all of them'
  ]
};

export const INITIAL_CONDITION = {
  field: '',
  modifier: 'equals',
  value: '',
};
