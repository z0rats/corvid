import React from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';

export default function LoadingState({ minHeight = '250px', height, size }) {
  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight={height ? undefined : minHeight} height={height}>
      <CircularProgress size={size} />
    </Box>
  );
}
