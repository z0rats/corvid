import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import CancelIcon from '@mui/icons-material/Cancel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const STAGE_KEYS = {
  resolving: 'scan.progress.resolving',
  friends: 'scan.progress.friends',
  profiles: 'scan.progress.profiles',
  mutual: 'scan.progress.mutual',
  scoring: 'scan.progress.scoring',
};

function stageLabel(t, scan) {
  const key = STAGE_KEYS[scan.stage];
  if (!key) return null;
  return t(key, {
    count: scan.friendsTotal,
    analyzed: scan.analyzed,
    total: scan.candidatesSelected || scan.friendsTotal,
  });
}

export default function LiveScanView({ scan, cancelScan }) {
  const { t } = useTranslation('steamRecon');
  const { phase, stage, analyzed, candidatesSelected, error } = scan;
  const progress = candidatesSelected > 0 ? Math.min(100, (analyzed / candidatesSelected) * 100) : 0;
  const determinate = stage === 'mutual' && candidatesSelected > 0;

  return (
    <Box>
      {phase === 'running' && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant={determinate ? 'determinate' : 'indeterminate'} value={progress} />
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 0.5 }}>
            <Typography variant="caption">{stageLabel(t, scan)}</Typography>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              {t('scan.progress.cancelButton')}
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
        <Chip icon={<CancelIcon />} color="warning" label={t('scan.cancelled')} sx={{ mb: 2 }} />
      )}

      {phase === 'completed' && (
        <Chip icon={<CheckCircleIcon />} color="success" label={t('scan.completed')} sx={{ mb: 2 }} />
      )}
    </Box>
  );
}
