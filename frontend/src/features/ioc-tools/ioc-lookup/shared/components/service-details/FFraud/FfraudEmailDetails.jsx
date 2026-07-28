import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import GroupIcon from '@mui/icons-material/Group';
import ReportIcon from '@mui/icons-material/Report';
import VerifiedIcon from '@mui/icons-material/Verified';
import NoDetails from '../NoDetails';

export default function FfraudEmailDetails({ result }) {
  const { t } = useTranslation('iocTools');
  const yes = t('providers.common.yes');
  const no = t('providers.common.no');

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

  return (
    <Box sx={{ p: 1 }}>
      <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider', maxWidth: 500 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <VerifiedIcon />
            <Typography variant="h6" component="h2">{t('providers.ffraud.emailChecks')}</Typography>
          </Box>
          <List disablePadding dense>
            <ListItem>
              <ListItemIcon sx={{ minWidth: 36 }}><DeleteSweepIcon color="action" /></ListItemIcon>
              <ListItemText primary={t('providers.ffraud.disposable')} secondary={result.is_disposable ? yes : no} />
            </ListItem>
            <ListItem>
              <ListItemIcon sx={{ minWidth: 36 }}><CheckCircleIcon color="action" /></ListItemIcon>
              <ListItemText primary={t('providers.ffraud.validFormat')} secondary={result.valid_format ? yes : no} />
            </ListItem>
            <ListItem>
              <ListItemIcon sx={{ minWidth: 36 }}><GroupIcon color="action" /></ListItemIcon>
              <ListItemText primary={t('providers.ffraud.roleAddress')} secondary={result.is_role_address ? yes : no} />
            </ListItem>
            <ListItem>
              <ListItemIcon sx={{ minWidth: 36 }}><VerifiedIcon color="action" /></ListItemIcon>
              <ListItemText primary={t('providers.ffraud.safeDomain')} secondary={result.safe_domain ? yes : no} />
            </ListItem>
            <ListItem>
              <ListItemIcon sx={{ minWidth: 36 }}><ReportIcon color="action" /></ListItemIcon>
              <ListItemText
                primary={t('providers.ffraud.communityBlacklisted')}
                secondary={result.community_blacklisted
                  ? t('providers.ffraud.blacklistReports', { count: result.blacklist_reports ?? 0 })
                  : no}
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Box>
  );
}
