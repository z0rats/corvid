import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Button from '@mui/material/Button';
import CancelIcon from '@mui/icons-material/Cancel';

import ScanForm from './ScanForm';
import ResultsView from './ResultsView';
import { useInstagramScan } from '../hooks/ui/useInstagramScan';
import PageHeader from '../../../core/components/ui/PageHeader';

export default function NewScan() {
  const { t } = useTranslation('instagramSearch');
  const { result, loading, error, scan, cancelScan } = useInstagramScan();

  return (
    <Box>
      <PageHeader title={t('scanForm.page.title')} description={t('scanForm.page.description')} />

      <ScanForm onScan={scan} disabled={loading} />

      {loading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress sx={{ mb: 0.5 }} />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              {t('scanForm.cancelButton')}
            </Button>
          </Box>
        </Box>
      )}
      {error && <Typography color="error" sx={{ mb: 2 }}>{error}</Typography>}

      <ResultsView result={result} />
    </Box>
  );
}
