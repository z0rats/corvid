import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import DnsIcon from '@mui/icons-material/Dns';
import RouterIcon from '@mui/icons-material/Router';
import SmartphoneIcon from '@mui/icons-material/Smartphone';
import TorIcon from '@mui/icons-material/Security';
import ProxyIcon from '@mui/icons-material/SignalWifi4Bar';
import VpnIcon from '@mui/icons-material/VpnKey';
import AbuseIcon from '@mui/icons-material/Warning';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { useTheme } from '@mui/material/styles';
import GeneralInfo from '../../GeneralInfo';
import NoDetails from '../NoDetails';

const getCircleFillColor = (score, chart) => {
  if (score === null || typeof score === 'undefined') return chart.inactive;
  if (score < 25) return chart.low;
  if (score < 75) return chart.medium;
  return chart.high;
};

export default function FfraudIpDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const yes = t('providers.common.yes');
  const no = t('providers.common.no');
  const theme = useTheme();
  const chart = theme.palette.chart;

  if (!result || result.error) {
    const message = result?.error
      ? t('providers.ffraud.errorFetching', { error: result.message || result.error })
      : t('providers.ffraud.unavailable');
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }

  const score = result.fraud_score ?? null;
  const geo = result.geo ?? {};

  const transformedData = {
    ip: ioc,
    country: geo.country,
    city: geo.city,
    isp: result.ISP,
    organisation: result.organization,
    asn: { asn: result.ASN },
  };

  const pieData = [
    { name: 'Score', value: score ?? 0 },
    { name: 'Remaining', value: 100 - (score ?? 0), fill: chart.inactive },
  ];

  return (
    <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2, p: 1 }}>
      <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 40%' } }}>
        <GeneralInfo data={transformedData} />
      </Box>

      <Card sx={{ flex: { xs: '1 1 100%', md: '1 1 60%' }, p: 2, borderRadius: 1, boxShadow: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DataUsageIcon />
          <Typography variant="h6" component="h2">{t('providers.ffraud.fraudScoreAndIndicators')}</Typography>
        </Box>

        {result.reason && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>{result.reason}</Typography>
        )}

        {result.threat_tags?.length > 0 && (
          <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap', gap: 1 }}>
            {result.threat_tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" color="warning" variant="outlined" />
            ))}
          </Stack>
        )}

        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid size={6}>
            <List disablePadding dense>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}><ProxyIcon color="action" /></ListItemIcon>
                <ListItemText primary={t('providers.ffraud.proxy')} secondary={result.proxy ? yes : no} />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}><VpnIcon color="action" /></ListItemIcon>
                <ListItemText
                  primary={t('providers.ffraud.vpn')}
                  secondary={result.vpn_provider || (result.vpn ? yes : no)}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}><TorIcon color="action" /></ListItemIcon>
                <ListItemText primary={t('providers.ffraud.tor')} secondary={result.tor ? yes : no} />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}><RouterIcon color="action" /></ListItemIcon>
                <ListItemText primary={t('providers.ffraud.relay')} secondary={result.relay ? yes : no} />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}><DnsIcon color="action" /></ListItemIcon>
                <ListItemText
                  primary={t('providers.ffraud.hosting')}
                  secondary={result.cloud_provider || (result.hosting ? yes : no)}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}><SmartphoneIcon color="action" /></ListItemIcon>
                <ListItemText primary={t('providers.ffraud.mobile')} secondary={result.mobile ? yes : no} />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}><AbuseIcon color="action" /></ListItemIcon>
                <ListItemText primary={t('providers.ffraud.recentAbuse')} secondary={result.recent_abuse ? yes : no} />
              </ListItem>
            </List>
          </Grid>
          <Grid size={6} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ResponsiveContainer width={180} height={180}>
              <PieChart width={180} height={180}>
                <Pie
                  data={pieData}
                  dataKey="value"
                  cx="50%"
                  cy="50%"
                  startAngle={90}
                  endAngle={-270}
                  innerRadius="70%"
                  outerRadius="100%"
                  paddingAngle={score === 0 || score === 100 ? 0 : 2}
                  stroke="none"
                >
                  <Cell fill={getCircleFillColor(score, chart)} />
                  <Cell fill={chart.inactive} />
                </Pie>
                <foreignObject width="100%" height="100%" style={{ textAlign: 'center' }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%', width: '100%' }}>
                    <Typography variant="h3" sx={{ color: getCircleFillColor(score, chart) }}>
                      {score ?? notAvailable}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('providers.ffraud.fraudRisk')}
                    </Typography>
                  </Box>
                </foreignObject>
              </PieChart>
            </ResponsiveContainer>
          </Grid>
        </Grid>
      </Card>
    </Box>
  );
}
