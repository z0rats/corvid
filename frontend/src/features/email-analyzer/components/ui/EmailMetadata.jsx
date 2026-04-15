import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

const METADATA_FIELDS = [
  { key: 'from', label: 'From' },
  { key: 'return-path', label: 'Reply To' },
  { key: 'to', label: 'To' },
  { key: 'cc', label: 'CC' },
  { key: 'date', label: 'Date' },
  { key: 'subject', label: 'Subject' },
];

function getDeliveredTo(result) {
  const deliveredTo = result['delivered-to'] || '';
  const rcptTo = result['rcpt-to'] || '';
  return deliveredTo || rcptTo || 'N/A';
}

function MetadataRow({ label, value }) {
  return (
    <Box sx={{ display: 'flex', py: 0.75, gap: 2 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 90, flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
        {value || 'N/A'}
      </Typography>
    </Box>
  );
}

export default function EmailMetadata({ result }) {
  return (
    <Box>
      {METADATA_FIELDS.map(({ key, label }) => (
        <MetadataRow key={key} label={label} value={result[key]} />
      ))}
      <MetadataRow label="Delivered to" value={getDeliveredTo(result)} />
    </Box>
  );
}
