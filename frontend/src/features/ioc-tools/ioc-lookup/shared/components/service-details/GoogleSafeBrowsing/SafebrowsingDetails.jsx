import React from "react";
import { useTranslation } from 'react-i18next';

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Grid from "@mui/material/Grid";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';

import NoDetails from "../NoDetails";

const ThreatMatchItem = ({ match, index, t, notAvailable }) => (
  <Card variant="outlined" sx={{ mb: 2, p:1, borderColor: 'warning.main' }}>
    <Typography variant="subtitle1" gutterBottom color="warning.dark" fontWeight="bold">
      {t('providers.googleSafeBrowsing.match', { number: index + 1, threatType: match.threatType })}
    </Typography>
    <List dense disablePadding>
      <ListItem sx={{py:0.5}}>
        <ListItemText primary={t('providers.googleSafeBrowsing.platformType')} secondary={match.platformType || notAvailable} />
      </ListItem>
      <ListItem sx={{py:0.5}}>
        <ListItemText primary={t('providers.googleSafeBrowsing.threatEntryType')} secondary={match.threatEntryType || notAvailable} />
      </ListItem>
      {match.threat && match.threat.url && (
         <ListItem sx={{py:0.5}}>
            <ListItemText primary={t('providers.googleSafeBrowsing.matchedUrlPattern')} secondary={match.threat.url} sx={{wordBreak: 'break-all'}} />
        </ListItem>
      )}
       {match.cacheDuration && (
         <ListItem sx={{py:0.5}}>
            <ListItemText primary={t('providers.googleSafeBrowsing.cacheDuration')} secondary={match.cacheDuration} />
        </ListItem>
      )}
    </List>
  </Card>
);


export default function SafeBrowseDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');

  if (!result) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.googleSafeBrowsing.loading')} />
      </Box>
    );
  }

  if (result.error) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.googleSafeBrowsing.errorFetching', { error: result.message || result.error })} />
      </Box>
    );
  }

  const hasMatches = result.matches && Array.isArray(result.matches) && result.matches.length > 0;

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
        <CardContent>
          <Grid container spacing={1} alignItems="center" mb={2}>
             {hasMatches ? <ReportProblemIcon color="warning" /> : <CheckCircleOutlineIcon color="success" />}
            <Typography variant="h6" component="div" sx={{ ml: 1 }}>
              {t('providers.googleSafeBrowsing.analysisFor')} <Typography component="span" sx={{wordBreak: 'break-all'}}>{ioc}</Typography>
            </Typography>
          </Grid>

          {hasMatches ? (
            <>
              <Typography variant="subtitle1" color="text.secondary" gutterBottom>
                {t('providers.googleSafeBrowsing.threatsReported')}
              </Typography>
              {result.matches.map((match, index) => (
                <ThreatMatchItem key={index} match={match} index={index} t={t} notAvailable={notAvailable} />
              ))}
            </>
          ) : (
            <Box display="flex" justifyContent="center" alignItems="center" flexDirection="column" p={2}>
              <CheckCircleOutlineIcon sx={{ fontSize: 40, color: 'success.main', mb:1 }} />
              <Typography variant="subtitle1" color="text.secondary">
                {t('providers.googleSafeBrowsing.noThreatsFound')}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
