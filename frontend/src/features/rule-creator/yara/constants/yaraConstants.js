// YARA Rule Builder Constants

export const STRING_TYPES = ['text', 'hex', 'regex', 'wide'];

export const STRING_MODIFIERS = ['nocase', 'ascii', 'wide', 'fullword'];

export const FILE_TYPES = ['exe', 'dll', 'pdf', 'doc', 'xls', 'ppt', 'zip', 'tar', 'rar'];

export const INITIAL_METADATA = {
  ruleName: '',
  author: '',
  description: '',
  reference: '',
  hash: '',
  version: '1.0',
};

export const INITIAL_CONDITIONS = {
  all: false,
  any: false,
  filesize: '',
  filetype: '',
};

export const INITIAL_STRING = {
  identifier: '',
  type: 'text',
  value: '',
  modifiers: [],
};

export const CONDITION_TYPES = {
  ALL: 'all',
  ANY: 'any',
  NONE: '',
};

export const FILE_TYPE_SIGNATURES = {
  exe: '5A4D', // MZ header
  dll: '5A4D', // MZ header
  pdf: '2550', // %PDF
  doc: 'D0CF', // OLE header
  xls: 'D0CF', // OLE header
  ppt: 'D0CF', // OLE header
  zip: '504B', // PK header
  tar: '7573', // ustar
  rar: '5261', // Rar!
};
