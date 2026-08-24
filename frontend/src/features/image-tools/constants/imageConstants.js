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
    MAX_SIZE: 50 * 1024 * 1024, // 50MB
  },

  HASH_TYPES: {
    MD5: 'MD5',
    SHA1: 'SHA1',
    SHA256: 'SHA256',
  },
};

// Keyless external tools that take a lat/lon and jump straight to that spot -
// same "one click, no API key" idea as REVERSE_SEARCH_ENGINES above, for GPS
// results instead of image URLs. MapChecking has no coordinate-based deep
// link (its URL hash encodes a drawn polygon, not a point), so it always
// opens the plain homepage instead.
export const GEO_EXTERNAL_TOOLS = [
  {
    name: 'ShadowMap',
    urlSearch: (lat, lon) => `https://app.shadowmap.org/?lat=${lat}&lng=${lon}&zoom=16`,
  },
  {
    name: 'Flightradar24',
    urlSearch: (lat, lon) => `https://www.flightradar24.com/multiview/${lat},${lon}/10`,
  },
  {
    name: 'Open Infrastructure Map',
    urlSearch: (lat, lon) => `https://openinframap.org/#16/${lat}/${lon}/L,O,P,S,T,W`,
  },
  {
    name: 'MapChecking',
    urlSearch: () => 'https://www.mapchecking.com/',
  },
];

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
