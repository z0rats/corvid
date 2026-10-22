import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

// A provider card with nothing to list: "no data", "not found", "not checked".
export function InfoCard({ title, hint }) {
  return (
    <Card sx={{ p: 2, m: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <InfoOutlinedIcon color="action" />
        <Typography variant="h6">{title}</Typography>
      </Box>
      {hint && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {hint}
        </Typography>
      )}
    </Card>
  );
}

// Answered by the backend without any request: the IP isn't public (`reserved: true`).
export function ReservedAddressCard() {
  const { t } = useTranslation('iocTools');
  return <InfoCard title={t('providers.ipContext.reserved')} hint={t('providers.ipContext.reservedHint')} />;
}
