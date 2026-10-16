import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Button from '@mui/material/Button';
import CancelIcon from '@mui/icons-material/Cancel';

import ScanForm from './ScanForm';
import ResultsView from './ResultsView';
import { useGitRecon } from '../hooks/useGitRecon';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';
import ScanQueuedNotice from '../../../core/components/ui/ScanQueuedNotice';
import PageHeader from '../../../core/components/ui/PageHeader';

export default function NewSearch() {
  const { t } = useTranslation('gitRecon');
  const { result, loading, queued, error, scan, cancelScan } = useGitRecon();

  // Hand-off from a command-palette pivot (e.g. "octocat github recon") — see crossFeatureNav.ts.
  // Defaults to 'nickname' mode, the closest match to a bare pivot value (a single GitHub
  // username) among the tool's three modes.
  const prefillValue = usePrefillFromQuery(useCallback((value) => scan({
    mode: 'nickname',
    target: value,
    include_forks: false,
    resolve_github_logins: true,
    ignore_noreply: true,
  }), [scan]));

  return (
    <Box>
      <PageHeader title={t('page.title')} description={t('page.description')} />

      <ScanForm
        onScan={scan}
        disabled={loading}
        initialTarget={prefillValue}
        initialMode={prefillValue ? 'nickname' : undefined}
      />

      {loading && (
        <Box sx={{ mb: 2 }}>
          {queued && <ScanQueuedNotice />}
          <LinearProgress sx={{ mb: 0.5 }} />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              {t('form.cancelButton')}
            </Button>
          </Box>
        </Box>
      )}
      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      <ResultsView result={result?.result} />
    </Box>
  );
}
