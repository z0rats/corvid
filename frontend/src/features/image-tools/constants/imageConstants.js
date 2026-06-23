export const IMAGE_CONSTANTS = {
  ACCEPTED_FILE_TYPES: {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/tiff': ['.tiff', '.tif'],
    'image/webp': ['.webp'],
    'image/heic': ['.heic'],
    'image/bmp': ['.bmp'],
    'image/gif': ['.gif'],
  },

  FILE_UPLOAD: {
    MAX_SIZE: 25 * 1024 * 1024, // 25MB
  },

  HASH_TYPES: {
    MD5: 'MD5',
    SHA1: 'SHA1',
    SHA256: 'SHA256',
  },
};

export const REVERSE_SEARCH_ENGINES = [
  {
    name: 'Google Lens',
    urlSearch: (url) => `https://lens.google.com/uploadbyurl?url=${encodeURIComponent(url)}`,
    uploadPage: 'https://images.google.com/',
  },
  {
    name: 'Yandex Images',
    urlSearch: (url) => `https://yandex.com/images/search?rpt=imageview&url=${encodeURIComponent(url)}`,
    uploadPage: 'https://yandex.com/images/',
  },
  {
    name: 'Bing Visual Search',
    urlSearch: (url) => `https://www.bing.com/images/search?q=imgurl:${encodeURIComponent(url)}&view=detailv2&iss=sbi`,
    uploadPage: 'https://www.bing.com/images/discover?form=Z9LH',
  },
  {
    name: 'TinEye',
    urlSearch: (url) => `https://tineye.com/search?url=${encodeURIComponent(url)}`,
    uploadPage: 'https://tineye.com/',
  },
];
