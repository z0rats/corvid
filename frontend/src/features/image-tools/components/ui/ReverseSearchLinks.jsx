import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { REVERSE_SEARCH_ENGINES } from '../../constants/imageConstants';

export default function ReverseSearchLinks({ imageUrl }) {
  const hasUrl = Boolean(imageUrl && imageUrl.trim());

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {hasUrl
          ? 'Open this image in a reverse-search engine:'
          : 'No image URL provided — these will open each engine so you can upload the file manually.'}
      </Typography>
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {REVERSE_SEARCH_ENGINES.map((engine) => (
          <Button
            key={engine.name}
            variant="outlined"
            size="small"
            endIcon={<OpenInNewIcon sx={{ fontSize: '0.875rem' }} />}
            href={hasUrl ? engine.urlSearch(imageUrl.trim()) : engine.uploadPage}
            target="_blank"
            rel="noopener noreferrer"
          >
            {engine.name}
          </Button>
        ))}
      </Box>
    </Box>
  );
}
