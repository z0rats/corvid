import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import WarningIcon from '@mui/icons-material/Warning';
import NoDetails from '../NoDetails';

export default function OpenPhishDetails({ result }) {
  const { t } = useTranslation('iocTools');

  if (!result || result.error) {
    const message = result?.error
      ? t('providers.openphish.errorFetching', { error: result.message || result.error })
      : t('providers.openphish.unavailable');
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }

  if (!result.listed) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.openphish.notListed')} />
      </Box>
    );
  }

  return (
    <Card elevation={0} sx={{ m: 1, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <WarningIcon color="error" />
          <Typography variant="h6" component="h2">{t('providers.openphish.listedTitle')}</Typography>
        </Box>

        <List dense disablePadding>
          {(result.matched_urls || []).map((url) => (
            <ListItem key={url} disableGutters>
              <ListItemText primary={url} />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
