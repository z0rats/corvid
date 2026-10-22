import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import CancelIcon from '@mui/icons-material/Cancel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

const STAGES = new Set(['profile', 'profile_done', 'posts', 'created', 'analyzing']);

export default function LiveScanView({ scan, cancelScan }) {
  const { t } = useTranslation('telegramSearch');
  const { phase, stage, sampled, sampleTarget, title, error } = scan;
  const determinate = stage === 'posts' && sampleTarget > 0;
  const progress = determinate ? Math.min(100, (sampled / sampleTarget) * 100) : 0;

  return (
    <Box>
      {phase === 'running' && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress variant={determinate ? 'determinate' : 'indeterminate'} value={progress} />
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 0.5 }}>
            <Typography variant="caption">
              {STAGES.has(stage)
                ? t(`progress.${stage}`, { title, sampled, target: sampleTarget })
                : null}
            </Typography>
            <Button size="small" color="error" startIcon={<CancelIcon />} onClick={cancelScan}>
              {t('progress.cancelButton')}
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
