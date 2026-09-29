import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

const LEVEL_COLOR = { high: 'error', medium: 'warning', low: 'success' };

function SignalRow({ signal, t }) {
  const hasData = signal.value !== null;
  return (
    <Stack spacing={0.5} sx={{ mb: 1.5 }}>
      <Stack direction="row" spacing={1} sx={{ justifyContent: 'space-between' }}>
        <Typography variant="body2">{t(`cheaterReport.signals.${signal.id}`)}</Typography>
        <Typography variant="caption" color="text.secondary">
          {hasData ? `${(signal.value * 100).toFixed(0)}%` : t('cheaterReport.signals.noData')}
        </Typography>
      </Stack>
      <LinearProgress
        variant="determinate"
        value={hasData ? signal.value * 100 : 0}
        sx={{ opacity: hasData ? 1 : 0.3 }}
      />
      <Typography variant="caption" color="text.secondary">
        {signal.explanation}
      </Typography>
    </Stack>
  );
}

export default function CheaterReportCard({ cheaterReport }) {
  const { t } = useTranslation('steamRecon');
  const { probability, level, coverage, already_banned: alreadyBanned, signals } = cheaterReport;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
        <Typography variant="h6" component="h2">
          {t('cheaterReport.title')}
        </Typography>
        <Chip size="small" color={LEVEL_COLOR[level] || 'default'} label={`${t(`cheaterReport.level.${level}`)} - ${(probability * 100).toFixed(0)}%`} />
      </Stack>

      <Alert severity="info" variant="outlined" sx={{ mb: 2 }}>
        {t('cheaterReport.disclaimer')}
      </Alert>

      {alreadyBanned && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {t('cheaterReport.alreadyBanned')}
        </Alert>
      )}

      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
        {t('cheaterReport.coverage', { percent: `${(coverage * 100).toFixed(0)}%` })}
      </Typography>

      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t('cheaterReport.signals.title')}
      </Typography>
      {signals.map((signal) => (
        <SignalRow key={signal.id} signal={signal} t={t} />
      ))}
    </Paper>
  );
}
