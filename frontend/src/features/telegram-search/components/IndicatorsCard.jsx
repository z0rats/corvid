import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';
import { indicatorPivotPath } from '../utils/telegramSearchConfig';

const ORDER = ['domains', 'urls', 'ips', 'emails', 'cves', 'md5', 'sha1', 'sha256'];

/** IOCs found in the sampled posts and description; a click sends one to IOC tools. */
export default function IndicatorsCard({ indicators }) {
  const { t } = useTranslation('telegramSearch');
  const navigate = useNavigate();
  const types = ORDER.filter((type) => indicators?.[type]?.length);
  if (types.length === 0) return null;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" component="h2" sx={{ mb: 0.5 }}>{t('indicators.title')}</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
        {t('indicators.hint')}
      </Typography>
      {types.map((type) => (
        <Box key={type} sx={{ mb: 1.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            {t(`indicators.types.${type}`)} ({indicators[type].length})
          </Typography>
          <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.75 }}>
            {indicators[type].map((value) => (
              <Chip
                key={value}
                size="small"
                variant="outlined"
                label={value}
                onClick={() => navigate(buildPrefillUrl(indicatorPivotPath(type), value))}
                sx={{ maxWidth: 360 }}
              />
            ))}
          </Stack>
        </Box>
      ))}
    </Paper>
  );
}
