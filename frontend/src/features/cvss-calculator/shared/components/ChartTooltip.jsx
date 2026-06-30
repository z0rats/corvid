import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTranslation } from 'react-i18next';

export default function ChartTooltip({ active, payload, label }) {
  const { t } = useTranslation('cvssCalculator');

  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Box
        sx={{
          backgroundColor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          p: 1,
          boxShadow: 2,
        }}
      >
        <Typography variant="body2" fontWeight="bold">
          {label}
        </Typography>
        <Typography variant="body2" color="primary">
          {t('chart.score', { score: data.normalizedScore.toFixed(2) })}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('chart.value', { value: data.displayValue })}
        </Typography>
      </Box>
    );
  }
  return null;
}
