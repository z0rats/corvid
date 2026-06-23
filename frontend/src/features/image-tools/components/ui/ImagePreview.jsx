import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

export default function ImagePreview({ previewUrl, fileInfo }) {
  if (!previewUrl) return null;

  return (
    <Paper elevation={1} sx={{ p: 2, mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
      <Box
        component="img"
        src={previewUrl}
        alt={fileInfo?.filename}
        sx={{ maxWidth: 160, maxHeight: 160, borderRadius: 1, objectFit: 'contain' }}
      />
      <Box>
        <Typography variant="subtitle1" fontWeight="medium">{fileInfo?.filename}</Typography>
        <Typography variant="body2" color="text.secondary">
          {fileInfo?.width}×{fileInfo?.height} · {fileInfo?.format}
        </Typography>
      </Box>
    </Paper>
  );
}
