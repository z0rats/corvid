import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import BugReportIcon from '@mui/icons-material/BugReport';
import BusinessIcon from '@mui/icons-material/Business';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import ComputerIcon from '@mui/icons-material/Computer';
import FolderZipIcon from '@mui/icons-material/FolderZip';
import GroupIcon from '@mui/icons-material/Group';
import LinkIcon from '@mui/icons-material/Link';
import SecurityIcon from '@mui/icons-material/Security';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import NoDetails from '../NoDetails';

const MAX_EMPLOYEE_URLS = 10;

function AttributionCaption({ t }) {
  return (
    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
      {t('providers.hudsonrock.attribution')}{' '}
      <Link href="https://www.hudsonrock.com/free-tools" target="_blank" rel="noopener noreferrer">
        hudsonrock.com/free-tools
      </Link>
    </Typography>
  );
}

function StealerCard({ stealer, t, notAvailable }) {
  return (
    <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, mb: 1.5 }}>
      <CardContent>
        <List disablePadding dense>
          <ListItem>
            <ListItemIcon sx={{ minWidth: 36 }}><CalendarTodayIcon color="action" fontSize="small" /></ListItemIcon>
            <ListItemText
              primary={t('providers.hudsonrock.dateCompromised')}
              secondary={stealer.date_compromised ? new Date(stealer.date_compromised).toLocaleDateString() : notAvailable}
            />
          </ListItem>
          <ListItem>
            <ListItemIcon sx={{ minWidth: 36 }}><ComputerIcon color="action" fontSize="small" /></ListItemIcon>
            <ListItemText
              primary={t('providers.hudsonrock.computerName')}
              secondary={`${stealer.computer_name || notAvailable} — ${stealer.operating_system || notAvailable}`}
            />
          </ListItem>
          <ListItem>
            <ListItemIcon sx={{ minWidth: 36 }}><FolderZipIcon color="action" fontSize="small" /></ListItemIcon>
            <ListItemText primary={t('providers.hudsonrock.malwarePath')} secondary={stealer.malware_path || notAvailable} />
          </ListItem>
          <ListItem>
            <ListItemIcon sx={{ minWidth: 36 }}><SecurityIcon color="action" fontSize="small" /></ListItemIcon>
            <ListItemText
              primary={t('providers.hudsonrock.antiviruses')}
              secondary={stealer.antiviruses?.length ? stealer.antiviruses.join(', ') : notAvailable}
            />
          </ListItem>
        </List>

        {stealer.top_logins?.length > 0 && (
          <Box sx={{ mt: 1 }}>
            <Stack
              direction="row"
              spacing={1}
              sx={{
                alignItems: "center",
                mb: 0.5
              }}>
              <VpnKeyIcon color="action" fontSize="small" />
              <Typography variant="body2" fontWeight="medium">{t('providers.hudsonrock.sampleLogins')}</Typography>
            </Stack>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
              {stealer.top_logins.map((login, idx) => (
                <Chip key={`${login}-${idx}`} label={login} size="small" variant="outlined" />
              ))}
            </Stack>
          </Box>
        )}

        <Stack direction="row" spacing={2} sx={{ mt: 1.5 }}>
          <Typography variant="caption" color="text.secondary">
            {t('providers.hudsonrock.userServices', { count: stealer.total_user_services ?? 0 })}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('providers.hudsonrock.corporateServices', { count: stealer.total_corporate_services ?? 0 })}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

function StealersView({ result, t, notAvailable }) {
  const stealers = result.stealers || [];

  if (stealers.length === 0) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.hudsonrock.noExposureFound')} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 1 }}>
      <Stack
        direction="row"
        spacing={1}
        sx={{
          alignItems: "center",
          mb: 1
        }}>
        <BugReportIcon color="error" />
        <Typography variant="h6" component="h2">
          {t('providers.hudsonrock.infectionsFound', { count: stealers.length })}
        </Typography>
      </Stack>
      {stealers.map((stealer, idx) => (
        <StealerCard key={idx} stealer={stealer} t={t} notAvailable={notAvailable} />
      ))}
      <AttributionCaption t={t} />
    </Box>
  );
}

function DomainView({ result, t }) {
  const total = result.total || 0;
  const employeeUrls = (result.data?.employees_urls || [])
    .slice()
    .sort((a, b) => (b.occurrence || 0) - (a.occurrence || 0))
    .slice(0, MAX_EMPLOYEE_URLS);

  if (total === 0) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.hudsonrock.noExposureFound')} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 1 }}>
      <Stack
        direction="row"
        spacing={1}
        sx={{
          alignItems: "center",
          mb: 1
        }}>
        <BugReportIcon color="error" />
        <Typography variant="h6" component="h2">
          {t('providers.hudsonrock.domainInfectionsFound', { count: total })}
        </Typography>
      </Stack>

      <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, mb: 1.5 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid size={4}>
              <Stack direction="row" spacing={1} sx={{
                alignItems: "center"
              }}>
                <BusinessIcon color="action" fontSize="small" />
                <Box>
                  <Typography variant="h6">{result.employees || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">{t('providers.hudsonrock.employees')}</Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid size={4}>
              <Stack direction="row" spacing={1} sx={{
                alignItems: "center"
              }}>
                <GroupIcon color="action" fontSize="small" />
                <Box>
                  <Typography variant="h6">{result.users || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">{t('providers.hudsonrock.users')}</Typography>
                </Box>
              </Stack>
            </Grid>
            <Grid size={4}>
              <Stack direction="row" spacing={1} sx={{
                alignItems: "center"
              }}>
                <GroupIcon color="action" fontSize="small" />
                <Box>
                  <Typography variant="h6">{result.third_parties || 0}</Typography>
                  <Typography variant="caption" color="text.secondary">{t('providers.hudsonrock.thirdParties')}</Typography>
                </Box>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {employeeUrls.length > 0 && (
        <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
          <CardContent>
            <Stack
              direction="row"
              spacing={1}
              sx={{
                alignItems: "center",
                mb: 1
              }}>
              <LinkIcon color="action" fontSize="small" />
              <Typography variant="body2" fontWeight="medium">{t('providers.hudsonrock.topEmployeeUrls')}</Typography>
            </Stack>
            <List disablePadding dense>
              {employeeUrls.map((entry, idx) => (
                <ListItem key={`${entry.url}-${idx}`} sx={{ px: 0 }}>
                  <ListItemText
                    primary={entry.url}
                    secondary={t('providers.hudsonrock.occurrences', { count: entry.occurrence || 0 })}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
      <AttributionCaption t={t} />
    </Box>
  );
}

export default function HudsonRockDetails({ result }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');

  if (!result || result.success === false || result.error) {
    const message = (result?.error || result?.success === false)
      ? t('providers.hudsonrock.errorFetching', { error: result?.message || result?.error || '' })
      : t('providers.hudsonrock.unavailable');
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }

  if (result.data) {
    return <DomainView result={result} t={t} />;
  }

  return <StealersView result={result} t={t} notAvailable={notAvailable} />;
}
