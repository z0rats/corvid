import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import WarningIcon from '@mui/icons-material/Warning';
import NoDetails from '../NoDetails';

export default function CisaKevDetails({ result }) {
  const { t } = useTranslation('iocTools');

  if (!result || result.error) {
    const message = result?.error
      ? t('providers.cisakev.errorFetching', { error: result.message || result.error })
      : t('providers.cisakev.unavailable');
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }

  if (!result.listed) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.cisakev.notListed')} />
      </Box>
    );
  }

  return (
    <Card elevation={0} sx={{ m: 1, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexWrap: 'wrap' }}>
          <WarningIcon color="error" />
          <Typography variant="h6" component="h2">{t('providers.cisakev.listedTitle')}</Typography>
          {result.knownRansomwareCampaignUse === 'Known' && (
            <Chip label={t('providers.cisakev.ransomwareUse')} color="error" size="small" />
          )}
        </Box>

        {result.vulnerabilityName && (
          <Typography variant="subtitle1" gutterBottom>{result.vulnerabilityName}</Typography>
        )}
        {result.shortDescription && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {result.shortDescription}
          </Typography>
        )}

        <List dense disablePadding>
          {result.vendorProject && (
            <ListItem disableGutters>
              <ListItemText
                primary={t('providers.cisakev.vendorProject')}
                secondary={[result.vendorProject, result.product].filter(Boolean).join(' / ')}
              />
            </ListItem>
          )}
          {result.dateAdded && (
            <ListItem disableGutters>
              <ListItemText primary={t('providers.cisakev.dateAdded')} secondary={result.dateAdded} />
            </ListItem>
          )}
          {result.dueDate && (
            <ListItem disableGutters>
              <ListItemText primary={t('providers.cisakev.dueDate')} secondary={result.dueDate} />
            </ListItem>
          )}
          {result.requiredAction && (
            <ListItem disableGutters>
              <ListItemText primary={t('providers.cisakev.requiredAction')} secondary={result.requiredAction} />
            </ListItem>
          )}
        </List>
      </CardContent>
    </Card>
  );
}
