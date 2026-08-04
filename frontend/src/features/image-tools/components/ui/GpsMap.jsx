import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import PlaceIcon from '@mui/icons-material/Place';

const MAP_BBOX_DEGREES = 0.01; // ~1km padding around the point

function buildEmbedUrl(latitude, longitude) {
  const bbox = [
    longitude - MAP_BBOX_DEGREES,
    latitude - MAP_BBOX_DEGREES,
    longitude + MAP_BBOX_DEGREES,
    latitude + MAP_BBOX_DEGREES,
  ].join(',');
  return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${latitude},${longitude}`;
}

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
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
        <PlaceIcon color="primary" />
        <Box>
          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
            {gps.latitude.toFixed(6)}, {gps.longitude.toFixed(6)}
            {gps.altitude !== null && gps.altitude !== undefined ? ` ${t('gps.altitude', { value: gps.altitude.toFixed(1) })}` : ''}
          </Typography>
          {gps.address && (
            <Typography variant="body2" color="text.secondary">{gps.address}</Typography>
          )}
          <Link href={gps.map_url} target="_blank" rel="noopener noreferrer" variant="body2">
            {t('gps.viewOnMap')}
          </Link>
        </Box>
      </Box>
      <Box
        component="iframe"
        title={t('gps.embeddedMapTitle')}
        src={buildEmbedUrl(gps.latitude, gps.longitude)}
        sx={{ width: '100%', height: 320, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}
      />
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
        {t('gps.embeddedMapHint')}
      </Typography>
    </Box>
  );
}
