import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import NoDetails from '../NoDetails';

export default function FirstEpssDetails({ result }) {
  const { t } = useTranslation('iocTools');

  if (!result || result.error) {
    const message = result?.error
      ? t('providers.firstepss.errorFetching', { error: result.message || result.error })
      : t('providers.firstepss.unavailable');
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }

  const entry = result.data?.[0];
  if (!entry) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.firstepss.notFound')} />
      </Box>
    );
  }

  const epssPct = (parseFloat(entry.epss) * 100).toFixed(2);
  const percentilePct = (parseFloat(entry.percentile) * 100).toFixed(1);

  return (
    <Card elevation={0} sx={{ m: 1, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>{t('providers.firstepss.title')}</Typography>
        <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="h3">{epssPct}%</Typography>
            <Typography variant="body2" color="text.secondary">{t('providers.firstepss.epssScore')}</Typography>
          </Box>
          <Box>
            <Typography variant="h3">{percentilePct}%</Typography>
            <Typography variant="body2" color="text.secondary">{t('providers.firstepss.percentile')}</Typography>
          </Box>
        </Box>
        {entry.date && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            {t('providers.firstepss.asOf', { date: entry.date })}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
