import React from 'react'; 
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid2';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import LocationCityIcon from '@mui/icons-material/LocationCity';
import BotIcon from '@mui/icons-material/SmartToy';
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
  if (score === 0) return chart.low;
  if (score >= 1 && score <= 50) return chart.medium;
  return chart.high;
};

export default function IpQualityscoreDetails({ result, ioc }) {
  const theme = useTheme();
  const chart = theme.palette.chart;

  if (!result || result.error) {
    const message = result && result.error 
        ? `Error fetching IPQualityScore details: ${result.message || result.error}` 
        : "IPQualityScore details are unavailable or data is incomplete.";
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }

  const score = result.fraud_score ?? null;

  const transformedData = {
    ip: ioc, 
    country: result.country_code, 
    city: result.city,
    isp: result.ISP, 
    organization: result.organization,
  };

  const pieData = [
    { name: "Score", value: score ?? 0 },
    { name: "Remaining", value: 100 - (score ?? 0), fill: chart.inactive }
  ];

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: { xs: 'column', md: 'row' },
      gap: 2, 
      p:1 
    }}>
      <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 40%' } }}>
        <GeneralInfo data={transformedData} />
      </Box>

      <Card sx={{ flex: { xs: '1 1 100%', md: '1 1 60%' }, p: 2, borderRadius: 1, boxShadow: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DataUsageIcon />
            <Typography variant="h6" component="h2">Fraud Score & Indicators</Typography>
          </Box>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={6}>
              <List disablePadding dense>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}><ProxyIcon color="action" /></ListItemIcon>
                  <ListItemText
                    primary="Proxy"
                    secondary={result.proxy ? "Yes" : "No"}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}><VpnIcon color="action" /></ListItemIcon>
                  <ListItemText
                    primary="VPN"
                    secondary={`${result.VPN ? "Yes" : "No"} ${result.active_VPN ? "(Active)" : ""}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}><TorIcon color="action" /></ListItemIcon>
                  <ListItemText
                    primary="Tor"
                    secondary={`${result.tor ? "Yes" : "No"} ${result.active_tor ? "(Active)" : ""}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}><AbuseIcon color="action" /></ListItemIcon>
                  <ListItemText
                    primary="Recent Abuse"
                    secondary={result.recent_abuse ? "Yes" : "No"}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}><BotIcon color="action" /></ListItemIcon>
                  <ListItemText
                    primary="Bot Status"
                    secondary={result.bot_status ? "Yes" : "No"}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon sx={{minWidth: 36}}><LocationCityIcon color="action" /></ListItemIcon>
                  <ListItemText
                    primary="Mobile Connection"
                    secondary={result.mobile ? "Yes" : "No"}
                  />
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
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        height: '100%',
                        width: '100%',
                      }}
                    >
                      <Typography variant="h3" sx={{ color: getCircleFillColor(score, chart) }}>
                        {score ?? 'N/A'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        fraud risk
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
