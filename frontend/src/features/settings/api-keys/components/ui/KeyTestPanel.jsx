import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';

/** "Test all" bar above the service cards; per-service results render on each card. */
export default function KeyTestPanel({ onTestAll, testingAll, error }) {
  const { t } = useTranslation('settings');

  return (
    <Paper elevation={0} sx={{ p: 2, mb: 3 }}>
      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle1" fontWeight={600}>{t('keyTest.title')}</Typography>
        <Button
          size="small"
          startIcon={testingAll ? <CircularProgress size={14} /> : <NetworkCheckIcon fontSize="small" />}
          onClick={onTestAll}
          disabled={testingAll}
        >
          {t('keyTest.testAll')}
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary">
        {t('keyTest.description')}
      </Typography>
      {error && (
        <Typography variant="body2" color="error.main" sx={{ mt: 1 }}>{error}</Typography>
      )}
    </Paper>
  );
}
