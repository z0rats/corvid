import React from 'react';
import Card from '@mui/material/Card';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import LanIcon from '@mui/icons-material/Lan';
import BusinessIcon from '@mui/icons-material/Business';
import LanguageIcon from '@mui/icons-material/Language';
import LocationCityIcon from '@mui/icons-material/LocationCity';
import DnsIcon from '@mui/icons-material/Dns';
import InfoIcon from '@mui/icons-material/Info';

export default function CrowdSecReputationCard({ result, ioc }) {
  const ipRangeScore = result.ip_range_score ?? 'N/A';

  return (
    <Card sx={{ p: 2, borderRadius: 2, height: '100%', border: '1px solid', borderColor: 'divider' }}>
      <Typography variant="h6" component="h3" gutterBottom>
        IP Reputation Details ({result.ip || ioc})
      </Typography>
      <List dense>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><LanIcon /></ListItemIcon>
          <ListItemText primary="IP Range Score" secondary={`${ipRangeScore}/5`} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><BusinessIcon /></ListItemIcon>
          <ListItemText primary="AS Name" secondary={result.as_name || "N/A"} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><LanguageIcon /></ListItemIcon>
          <ListItemText primary="Country" secondary={result.location?.country || "N/A"} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><LocationCityIcon /></ListItemIcon>
          <ListItemText primary="City" secondary={result.location?.city || "N/A"} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><DnsIcon /></ListItemIcon>
          <ListItemText primary="Reverse DNS" secondary={result.location?.reverse_dns || "N/A"} sx={{ wordBreak: 'break-all' }} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><InfoIcon /></ListItemIcon>
          <ListItemText primary="Remediation" secondary={result.remediation || "N/A"} />
        </ListItem>
      </List>
    </Card>
  );
}
