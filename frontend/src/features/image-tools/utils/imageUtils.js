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
};
