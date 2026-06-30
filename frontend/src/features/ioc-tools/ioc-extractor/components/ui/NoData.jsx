import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import NotInterestedIcon from '@mui/icons-material/NotInterested';

export default function NoData() {
  const { t } = useTranslation('iocTools');

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
      <NotInterestedIcon sx={{ fontSize: 48, color: 'grey.400' }} />
      <Box>
        <Typography variant="subtitle1" fontWeight={500}>
          {t('iocExtractor.noData.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('iocExtractor.noData.message')}
        </Typography>
      </Box>
    </Box>
  );
}
