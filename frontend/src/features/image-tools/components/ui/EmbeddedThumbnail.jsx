import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ImageIcon from '@mui/icons-material/Image';

export default function EmbeddedThumbnail({ hasThumbnail, thumbnailBase64 }) {
  const { t } = useTranslation('imageTools');

  if (!hasThumbnail || !thumbnailBase64) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2, p: 1.5, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
      <Box
        component="img"
        src={thumbnailBase64}
        alt={t('exif.thumbnailAlt')}
        sx={{ maxWidth: 100, maxHeight: 100, borderRadius: 1, objectFit: 'contain' }}
      />
      <Box>
        <Typography variant="body2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <ImageIcon fontSize="small" color="action" />
          {t('exif.thumbnailTitle')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('exif.thumbnailHint')}
        </Typography>
      </Box>
    </Box>
  );
}
