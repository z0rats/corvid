import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import { useTranslation } from 'react-i18next';

export default function RecordingBanner({ stepCount, onStop }) {
  const { t } = useTranslation('commandPalette');

  return (
    <Box sx={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      px: 2, py: 0.75, bgcolor: 'error.main', color: 'error.contrastText',
    }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <FiberManualRecordIcon fontSize="small" />
        <Typography variant="body2">{t('recording.banner', { count: stepCount })}</Typography>
      </Box>
      <Button size="small" color="inherit" onClick={onStop}>
        {t('recording.stop')}
      </Button>
    </Box>
  );
}
