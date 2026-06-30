import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import PlaceIcon from '@mui/icons-material/Place';

export default function GpsMap({ gps }) {
  const { t } = useTranslation('imageTools');

  if (!gps) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t('gps.empty')}
      </Typography>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <PlaceIcon color="primary" />
      <Box>
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {gps.latitude.toFixed(6)}, {gps.longitude.toFixed(6)}
          {gps.altitude !== null && gps.altitude !== undefined ? ` ${t('gps.altitude', { value: gps.altitude.toFixed(1) })}` : ''}
        </Typography>
        <Link href={gps.map_url} target="_blank" rel="noopener noreferrer" variant="body2">
          {t('gps.viewOnMap')}
        </Link>
      </Box>
    </Box>
  );
}
