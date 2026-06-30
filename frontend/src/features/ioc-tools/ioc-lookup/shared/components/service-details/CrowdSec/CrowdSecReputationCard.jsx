import React from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const ipRangeScore = result.ip_range_score ?? notAvailable;

  return (
    <Card sx={{ p: 2, borderRadius: 2, height: '100%', border: '1px solid', borderColor: 'divider' }}>
      <Typography variant="h6" component="h3" gutterBottom>
        {t('providers.crowdsec.ipReputationDetails', { ip: result.ip || ioc })}
      </Typography>
      <List dense>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><LanIcon /></ListItemIcon>
          <ListItemText primary={t('providers.crowdsec.ipRangeScore')} secondary={`${ipRangeScore}/5`} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><BusinessIcon /></ListItemIcon>
          <ListItemText primary={t('providers.crowdsec.asName')} secondary={result.as_name || notAvailable} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><LanguageIcon /></ListItemIcon>
          <ListItemText primary={t('providers.common.country')} secondary={result.location?.country || notAvailable} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><LocationCityIcon /></ListItemIcon>
          <ListItemText primary={t('providers.common.city')} secondary={result.location?.city || notAvailable} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><DnsIcon /></ListItemIcon>
          <ListItemText primary={t('providers.common.reverseDns')} secondary={result.location?.reverse_dns || notAvailable} sx={{ wordBreak: 'break-all' }} />
        </ListItem>
        <ListItem>
          <ListItemIcon sx={{ minWidth: 36 }}><InfoIcon /></ListItemIcon>
          <ListItemText primary={t('providers.crowdsec.remediation')} secondary={result.remediation || notAvailable} />
        </ListItem>
      </List>
    </Card>
  );
}
