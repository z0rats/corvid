import React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import GavelIcon from '@mui/icons-material/Gavel';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import NoDetails from '../NoDetails';

function DetailItem({ label, value }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <ListItem disableGutters dense>
      <ListItemText
        primary={<Typography variant="body2" component="span" fontWeight="bold">{label}:</Typography>}
        secondary={<Typography variant="body2" component="span" color="text.secondary" sx={{ ml: 1, wordBreak: 'break-all' }}>{value}</Typography>}
      />
    </ListItem>
  );
}

export default function BlacklistDetails({ result }) {
  if (!result || !result.data) {
    return <NoDetails message="Address blacklist details are unavailable or still loading." />;
  }

  const { data } = result;
  const { matched, sources = [], ofac, scamsniffer } = data;

  if (!matched) {
    return (
      <Card sx={{ p: 2, m: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircleIcon color="success" />
          <Typography variant="h6">No match — not listed in OFAC SDN or ScamSniffer</Typography>
        </Box>
      </Card>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, p: 1 }}>
      {sources.includes('OFAC') && ofac && (
        <Card sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <GavelIcon color="error" />
            <Typography variant="h6">OFAC Sanctioned</Typography>
            <Chip label="SDN" color="error" size="small" />
          </Box>
          <List dense disablePadding>
            <DetailItem label="Entity" value={ofac.entity_name} />
            <DetailItem label="Program" value={ofac.program} />
            <DetailItem label="Chain" value={ofac.chain} />
            <DetailItem label="Remarks" value={ofac.remarks} />
          </List>
        </Card>
      )}

      {sources.includes('SCAMSNIFFER') && scamsniffer && (
        <Card sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <WarningAmberIcon color="error" />
            <Typography variant="h6">Phishing-Associated Address</Typography>
            <Chip label="ScamSniffer" color="error" size="small" />
          </Box>
          <List dense disablePadding>
            <DetailItem label="Chain" value={scamsniffer.chain} />
            <DetailItem label="Phishing domain" value={scamsniffer.phishing_domain} />
          </List>
        </Card>
      )}
    </Box>
  );
}
