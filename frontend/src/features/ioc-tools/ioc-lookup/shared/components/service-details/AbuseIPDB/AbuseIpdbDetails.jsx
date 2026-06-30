import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import FileCopyIcon from '@mui/icons-material/FileCopyOutlined';
import PeopleIcon from '@mui/icons-material/PeopleOutlined';
import ScheduleIcon from '@mui/icons-material/ScheduleOutlined';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUserOutlined';
import { PieChart, Pie, ResponsiveContainer } from 'recharts';
import GeneralInfo from '../../GeneralInfo';
import NoDetails from '../NoDetails';

const getCircleFillColor = (score, chart) => {
  if (score === null || typeof score === 'undefined') return chart.inactive;
  if (score === 0) return chart.low;
  if (score >= 1 && score <= 59) return chart.medium;
  return chart.high;
};

export default function AbuseIpdbDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const chart = theme.palette.chart;

  if (!result || !result.data) {
    const message = result && result.error
        ? t('providers.abuseipdb.errorFetching', { error: result.message || result.error })
        : t('providers.abuseipdb.unavailable');
    return <NoDetails message={message} />;
  }

  const { data } = result;
  const score = data.abuseConfidenceScore ?? null;

  const transformedData = {
    ip: data.ipAddress,
    usageType: data.usageType,
    domain: data.domain,
    hostnames: data.hostnames || [],
    country: data.countryName,
    countryCode: data.countryCode,
    isp: data.isp,
  };

  const pieData = [
    { name: "Score", value: score ?? 0 },
    { name: "Remaining", value: 100 - (score ?? 0), fill: chart.inactive }
  ];

  const lastReportedDate = data.lastReportedAt ? new Date(data.lastReportedAt).toLocaleDateString() : t('providers.common.notAvailable');


  return (
    <Box sx={{
      display: 'flex',
      flexDirection: { xs: 'column', md: 'row' },
      gap: 2,
      p: 1
    }}>
      <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 50%' } }}>
        <GeneralInfo
          data={transformedData}
        />
      </Box>

      <Card  sx={{
        flex: { xs: '1 1 100%', md: '1 1 50%' },
        p: 2,
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DataUsageIcon />
          <Typography variant="h6" component="h2">{t('providers.abuseipdb.confidenceScoreAndStats')}</Typography>
        </Box>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid size={6}>
            <List disablePadding dense>
              <ListItem>
                <ListItemIcon sx={{minWidth: 36}}>
                  <FileCopyIcon color="action" />
                </ListItemIcon>
                <ListItemText
                  primary={t('providers.abuseipdb.totalReports')}
                  secondary={data.totalReports ?? t('providers.common.notAvailable')}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{minWidth: 36}}>
                  <PeopleIcon color="action" />
                </ListItemIcon>
                <ListItemText
                  primary={t('providers.abuseipdb.distinctUsers')}
                  secondary={data.numDistinctUsers ?? t('providers.common.notAvailable')}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{minWidth: 36}}>
                  <ScheduleIcon color="action" />
                </ListItemIcon>
                <ListItemText
                  primary={t('providers.abuseipdb.lastReported')}
                  secondary={lastReportedDate}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{minWidth: 36}}>
                  <VerifiedUserIcon
                    color={data.isWhitelisted ? "success" : "action"}
                  />
                </ListItemIcon>
                <ListItemText
                  primary={t('providers.abuseipdb.whitelisted')}
                  secondary={data.isWhitelisted ? t('providers.common.yes') : t('providers.common.no')}
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
                  startAngle={90}
                  endAngle={-270}
                  innerRadius="70%"
                  outerRadius="100%"
                  paddingAngle={score === 0 || score === 100 ? 0 : 2}
                  domain={[0, 100]}
                  stroke="none"
                  fill={getCircleFillColor(score, chart)}
                />
                <foreignObject
                  width="100%"
                  height="100%"
                  style={{ textAlign: "center" }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      height: "100%",
                      width: "100%",
                    }}
                  >
                    <Typography variant="h3" sx={{ color: getCircleFillColor(score, chart) }} align="center">
                      {score ?? t('providers.common.notAvailable')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" align="center">
                      {t('providers.abuseipdb.percentMalicious')}
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
