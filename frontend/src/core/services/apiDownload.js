import api from './baseApi';
import { downloadFile } from '../utils/exportData';

/** `filename="..."` from a Content-Disposition header, or null. */
export function filenameFromDisposition(header) {
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(header ?? '');
  if (!match) return null;
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
}

/** Download one API file through the authenticated client. A plain `<a href>` to `/api/*` can't
 * carry the access token's Authorization header and gets a 401, so every download goes here. */
export async function downloadFromApi(path, { params, fallbackName } = {}) {
  const response = await api.get(path, { params, responseType: 'blob' });
  const name = filenameFromDisposition(response.headers?.['content-disposition']) ?? fallbackName;
  downloadFile(response.data, name, response.data?.type || 'application/octet-stream');
}
