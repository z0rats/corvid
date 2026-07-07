import React from 'react';
import { useTranslation } from 'react-i18next';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import DnsIcon from '@mui/icons-material/Dns';
import InfoIcon from '@mui/icons-material/InfoOutlined';
import WebIcon from '@mui/icons-material/Language';
import GeoIcon from '@mui/icons-material/Public';
import TimeIcon from '@mui/icons-material/Schedule';
import RiskIcon from '@mui/icons-material/Security';

import NoDetails from '../NoDetails';

const DetailListItem = ({ icon, primary, secondary, secondaryIsBlock = false, notAvailable }) => (
  <ListItem dense disableGutters sx={{alignItems: secondaryIsBlock ? 'flex-start' : 'center'}}>
    <ListItemIcon sx={{minWidth: 36}}>{icon || <InfoIcon color="action" />}</ListItemIcon>
    <ListItemText
      primary={primary}
      secondary={secondary || notAvailable}
      primaryTypographyProps={{ variant: 'body2', fontWeight: 'medium' }}
      secondaryTypographyProps={{ variant: 'body2', color: 'text.secondary', component: secondaryIsBlock ? 'div' : 'span' }}
    />
  </ListItem>
);


export default function PulsediveDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');

  if (!result) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.pulsedive.loading')} />
      </Box>
    );
  }

  if (result.error) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.pulsedive.errorFetching', { error: result.message || result.error })} />
      </Box>
    );
  }

  if (result.status === "Not found" || !result.results || result.results.length === 0) {
     return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.pulsedive.notFound', { ioc })} />
      </Box>
    );
  }

  const data = result.results[0];

  const getProperty = (path, defaultValue = notAvailable) => {
    const value = path.split('.').reduce((obj, key) => (obj && obj[key] !== undefined) ? obj[key] : undefined, data.summary?.properties);
    return value ?? defaultValue;
  };

  const formatDate = (dateString) => {
    if (!dateString) return notAvailable;
    return new Date(dateString).toLocaleString();
  }

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
        <CardContent>
          <Grid container spacing={1} alignItems="center" mb={2}>
            <RiskIcon color="action" />
            <Typography variant="h6" component="div" sx={{ ml: 1 }}>
              {t('providers.pulsedive.analysisFor')} <Typography component="span" sx={{wordBreak: 'break-all'}}>{data.indicator || ioc}</Typography>
            </Typography>
          </Grid>

          <List dense>
            <DetailListItem
              icon={<RiskIcon />}
              primary={t('providers.pulsedive.riskLevel')}
              secondary={data.risk ? data.risk.charAt(0).toUpperCase() + data.risk.slice(1) : notAvailable}
              notAvailable={notAvailable}
            />
            <DetailListItem
              icon={<TimeIcon />}
              primary={t('providers.pulsedive.timestamps')}
              secondaryIsBlock={true}
              notAvailable={notAvailable}
              secondary={
                <Box>
                  <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.added')} {formatDate(data.stamp_added)}</Typography>
                  <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.updated')} {formatDate(data.stamp_updated)}</Typography>
                  <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.lastSeen')} {formatDate(data.stamp_seen)}</Typography>
                </Box>
              }
            />

            <Divider sx={{my:1}}/>
            <Typography variant="subtitle1" sx={{mt:1, mb:0.5, fontWeight:'medium'}}>{t('providers.pulsedive.properties')}</Typography>

            {data.summary?.properties?.dns && (
              <DetailListItem
                icon={<DnsIcon />}
                primary={t('providers.pulsedive.dnsPtr')}
                secondary={getProperty('dns.ptr')}
                notAvailable={notAvailable}
              />
            )}

            {data.summary?.properties?.geo && (
              <DetailListItem
                icon={<GeoIcon />}
                primary={t('providers.pulsedive.geolocation')}
                secondaryIsBlock={true}
                notAvailable={notAvailable}
                secondary={
                  <Box>
                    <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.country')} {getProperty('geo.country')} ({getProperty('geo.countrycode')})</Typography>
                    <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.city')} {getProperty('geo.city')}</Typography>
                    <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.organization')} {getProperty('geo.org')}</Typography>
                  </Box>
                }
              />
            )}

            {data.summary?.properties?.http && (
              <DetailListItem
                icon={<WebIcon />}
                primary={t('providers.pulsedive.httpProperties')}
                secondaryIsBlock={true}
                notAvailable={notAvailable}
                secondary={
                  <Box>
                    <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.contentType')} {getProperty('http.++content-type')}</Typography>
                    <Typography variant="caption" sx={{ display: 'block' }}>{t('providers.pulsedive.statusCode')} {getProperty('http.++code')}</Typography>
                  </Box>
                }
              />
            )}

            {Object.keys(data.summary?.properties || {}).length === 0 && (
                <Typography variant="caption" color="text.secondary" sx={{pl:5.5}}>{t('providers.pulsedive.noProperties')}</Typography>
            )}

          </List>
        </CardContent>
      </Card>
    </Box>
  );
}
