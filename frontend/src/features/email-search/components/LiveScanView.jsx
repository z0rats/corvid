import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';

import FoundProvidersList from './FoundProvidersList';

export default function LiveScanView({ scan }) {
  const { t } = useTranslation('emailSearch');
  const { phase, checked, totalProviders, currentProvider, foundProviders, error, cancelScan } = scan;
  const progress = totalProviders > 0 ? Math.min(100, (checked / totalProviders) * 100) : 0;

  return (
    <Box>
      {phase === 'running' && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 0.5 }}>
            <Typography variant="caption">
              {t('scan.progress', { checked, total: totalProviders })}
              {currentProvider ? ` — ${t('scan.checking', { provider: currentProvider })}` : ''}
            </Typography>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              {t('scan.cancelButton')}
            </Button>
          </Box>
        </Box>
      )}

      {phase === 'failed' && (
        <Typography color="error" sx={{ mb: 2 }}>
          {t('scan.failed', { error })}
        </Typography>
      )}

      {phase === 'cancelled' && (
        <Chip
          icon={<CancelIcon />}
          color="warning"
          label={t('scan.cancelled', { checked: totalProviders, found: foundProviders.length })}
          sx={{ mb: 2 }}
        />
      )}

      {phase === 'completed' && (
        <Chip
          icon={<CheckCircleIcon />}
          color="success"
          label={t('scan.completed', { checked: totalProviders, found: foundProviders.length })}
          sx={{ mb: 2 }}
        />
      )}

      <FoundProvidersList providers={foundProviders} />
    </Box>
  );
}
