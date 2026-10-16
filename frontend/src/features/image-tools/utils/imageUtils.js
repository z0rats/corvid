export const imageUtils = {
  formatFileSize: (bytes) => {
    if (!bytes || bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  groupExifTags: (exif) => {
    const groups = {};
    Object.entries(exif || {}).forEach(([tagName, value]) => {
      const [category, ...rest] = tagName.split(' ');
      const label = rest.join(' ') || tagName;
      if (!groups[category]) groups[category] = {};
      groups[category][label] = value;
    });
    return groups;
  },

  downloadBlob: (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  },

  // Human-readable name for an ISO region ('RS') or language ('sr') code via the
  // browser's own tables; falls back to the raw code where unsupported.
  displayName: (code, type, locale = 'en') => {
    try {
      return new Intl.DisplayNames([locale], { type, fallback: 'code' }).of(code) || code;
    } catch {
      return code;
    }
  },
};
