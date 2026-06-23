import { imageUtils } from './imageUtils';

describe('imageUtils.formatFileSize', () => {
  it('returns "0 Bytes" for zero or missing input', () => {
    expect(imageUtils.formatFileSize(0)).toBe('0 Bytes');
    expect(imageUtils.formatFileSize(undefined)).toBe('0 Bytes');
    expect(imageUtils.formatFileSize(null)).toBe('0 Bytes');
  });

  it('formats bytes', () => {
    expect(imageUtils.formatFileSize(500)).toBe('500 Bytes');
  });

  it('formats kilobytes', () => {
    expect(imageUtils.formatFileSize(2048)).toBe('2 KB');
  });

  it('formats megabytes', () => {
    expect(imageUtils.formatFileSize(5 * 1024 * 1024)).toBe('5 MB');
  });
});

describe('imageUtils.groupExifTags', () => {
  it('returns an empty object for empty/missing input', () => {
    expect(imageUtils.groupExifTags({})).toEqual({});
    expect(imageUtils.groupExifTags(undefined)).toEqual({});
  });

  it('groups tags by their category prefix', () => {
    const exif = {
      'Image Software': 'TestSoftware 1.0',
      'Image Make': 'TestCam',
      'EXIF DateTimeOriginal': '2024:01:01 12:00:00',
      'GPS GPSLatitude': '[40, 26, 46.3]',
    };

    const groups = imageUtils.groupExifTags(exif);

    expect(Object.keys(groups).sort()).toEqual(['EXIF', 'GPS', 'Image']);
    expect(groups.Image).toEqual({ Software: 'TestSoftware 1.0', Make: 'TestCam' });
    expect(groups.EXIF).toEqual({ DateTimeOriginal: '2024:01:01 12:00:00' });
    expect(groups.GPS).toEqual({ GPSLatitude: '[40, 26, 46.3]' });
  });

  it('falls back to the full tag name when there is no category prefix', () => {
    const groups = imageUtils.groupExifTags({ SingleWordTag: 'value' });

    expect(groups.SingleWordTag).toEqual({ SingleWordTag: 'value' });
  });
});
