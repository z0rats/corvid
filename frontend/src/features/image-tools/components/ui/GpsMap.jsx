import React from 'react';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import PlaceIcon from '@mui/icons-material/Place';

export default function GpsMap({ gps }) {
  if (!gps) {
    return (
      <Typography variant="body2" color="text.secondary">
        No GPS data found in this image.
      </Typography>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <PlaceIcon color="primary" />
      <Box>
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {gps.latitude.toFixed(6)}, {gps.longitude.toFixed(6)}
          {gps.altitude !== null && gps.altitude !== undefined ? ` (alt. ${gps.altitude.toFixed(1)} m)` : ''}
        </Typography>
        <Link href={gps.map_url} target="_blank" rel="noopener noreferrer" variant="body2">
          View on map
        </Link>
      </Box>
    </Box>
  );
}
