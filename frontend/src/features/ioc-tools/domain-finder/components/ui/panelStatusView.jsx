import React from 'react';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';

// What an auto-fetching panel shows before it has data (`useDomainPanel` state): nothing
// for an unsupported pattern or no result, a progress bar, or the error. Returns
// `undefined` once there's data to render, so a panel reads:
//   const status = panelStatusView(panel, t('...errorPrefix'));
//   if (status !== undefined) return status;
export function panelStatusView({ unsupported, loading, error, data }, errorPrefix) {
  if (unsupported) return null;
  if (loading) {
    return (
      <>
        <LinearProgress />
        <br />
      </>
    );
  }
  if (error) {
    return (
      <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
        {errorPrefix} {error}
      </Alert>
    );
  }
  if (!data) return null;
  return undefined;
}
