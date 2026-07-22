import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';

import ScanForm from './ScanForm';
import ResultsView from './ResultsView';
import { useGitRecon } from '../hooks/useGitRecon';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export default function NewSearch() {
  const { t } = useTranslation('gitRecon');
  const { result, loading, error, scan } = useGitRecon();
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

  useEffect(() => {
    // Hand-off from a command-palette pivot (e.g. "octocat github recon") — see
    // crossFeatureNav.js. Defaults to 'nickname' mode, the closest match to a bare pivot value
    // (a single GitHub username) among the tool's three modes.
    if (!prefillValue) return;
    scan({
      mode: 'nickname',
      target: prefillValue,
      include_forks: false,
      resolve_github_logins: true,
      ignore_noreply: true,
    });
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('page.description')}
      </Typography>

      <ScanForm
        onScan={scan}
        disabled={loading}
        initialTarget={prefillValue}
        initialMode={prefillValue ? 'nickname' : undefined}
      />

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      <ResultsView result={result?.result} />
    </Box>
  );
}
