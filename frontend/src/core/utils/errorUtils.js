export function extractErrorMessage(error, fallback = 'An unexpected error occurred') {
  return error.response?.data?.detail || error.message || fallback;
}
