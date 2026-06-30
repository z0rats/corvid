import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

const METADATA_FIELDS = [
  { key: 'from', i18nKey: 'from' },
  { key: 'return-path', i18nKey: 'replyTo' },
  { key: 'to', i18nKey: 'to' },
  { key: 'cc', i18nKey: 'cc' },
  { key: 'date', i18nKey: 'date' },
  { key: 'subject', i18nKey: 'subject' },
];

function getDeliveredTo(result, notAvailable) {
  const deliveredTo = result['delivered-to'] || '';
  const rcptTo = result['rcpt-to'] || '';
  return deliveredTo || rcptTo || notAvailable;
}

function MetadataRow({ label, value, notAvailable }) {
  return (
    <Box sx={{ display: 'flex', py: 0.75, gap: 2 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 90, flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
        {value || notAvailable}
      </Typography>
    </Box>
  );
}

export default function EmailMetadata({ result }) {
  const { t } = useTranslation('emailAnalyzer');
  const notAvailable = t('emailMetadata.notAvailable');

  return (
    <Box>
      {METADATA_FIELDS.map(({ key, i18nKey }) => (
        <MetadataRow key={key} label={t(`emailMetadata.fields.${i18nKey}`)} value={result[key]} notAvailable={notAvailable} />
      ))}
      <MetadataRow label={t('emailMetadata.fields.deliveredTo')} value={getDeliveredTo(result, notAvailable)} notAvailable={notAvailable} />
    </Box>
  );
}
