import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';

import ScanForm from './ScanForm';
import ResultsView from './ResultsView';
import { useGitRecon } from '../hooks/useGitRecon';

export default function NewSearch() {
  const { t } = useTranslation('gitRecon');
  const { result, loading, error, scan } = useGitRecon();

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('page.description')}
      </Typography>

      <ScanForm onScan={scan} disabled={loading} />

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      <ResultsView result={result?.result} />
    </Box>
  );
}
