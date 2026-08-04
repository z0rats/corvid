import api from '../../../../core/services/baseApi';

const FILENAME_PATTERN = /filename="?([^"]+)"?/;

export const imageMetadataRemovalApi = {
  /**
   * Returns { blob, filename } - responseType 'blob' means error bodies also
   * arrive as a Blob (not parsed JSON), see useImageMetadataRemoval for how
   * the `detail` message gets extracted from a failed request.
   */
  async removeMetadata(file, mode) {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { mode },
      responseType: 'blob',
    };

    const response = await api.post('/api/image/strip-metadata', formData, config);
    const disposition = response.headers['content-disposition'] || '';
    const match = disposition.match(FILENAME_PATTERN);

    return { blob: response.data, filename: match ? match[1] : file.name };
  }
};
