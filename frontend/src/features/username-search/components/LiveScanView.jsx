import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';

import FoundSitesList from './FoundSitesList';

export default function LiveScanView({ scan }) {
  const { t } = useTranslation('usernameSearch');
  const { phase, source, checked, totalSites, currentSite, foundSites, error, cancelScan } = scan;
  const isCoarseProgress = source === 'social_analyzer';
  const progress = totalSites > 0 ? Math.min(100, (checked / totalSites) * 100) : 0;

  return (
    <Box>
      {phase === 'running' && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant={isCoarseProgress ? 'indeterminate' : 'determinate'} value={progress} />
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 0.5 }}>
            <Typography variant="caption">
              {isCoarseProgress
                ? t('scan.scanning')
                : t('scan.progress', { checked, total: totalSites })}
              {!isCoarseProgress && currentSite ? ` — ${t('scan.checking', { site: currentSite })}` : ''}
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
          label={t('scan.cancelled', { checked: totalSites, found: foundSites.length })}
          sx={{ mb: 2 }}
        />
      )}

      {phase === 'completed' && (
        <Chip
          icon={<CheckCircleIcon />}
          color="success"
          label={t('scan.completed', { checked: totalSites, found: foundSites.length })}
          sx={{ mb: 2 }}
        />
      )}

      <FoundSitesList sites={foundSites} />
    </Box>
  );
}
