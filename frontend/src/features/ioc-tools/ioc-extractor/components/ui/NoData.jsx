import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import NotInterestedIcon from '@mui/icons-material/NotInterested';

export default function NoData() {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
      <NotInterestedIcon sx={{ fontSize: 48, color: 'grey.400' }} />
      <Box>
        <Typography variant="subtitle1" fontWeight={500}>
          No IOCs found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          There are no items for this IOC type.
        </Typography>
      </Box>
    </Box>
  );
}
