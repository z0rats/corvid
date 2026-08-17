import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import NoDetails from '../NoDetails';

export default function LibraryOfLeaksDetails({ result }) {
  const { t } = useTranslation('iocTools');

  if (!result) {
    return <NoDetails message={t('providers.libraryofleaks.unavailable')} />;
  }

  const { total_hits: totalHits = 0, collections = [], search_url: searchUrl } = result;

  if (totalHits === 0) {
    return (
      <Card sx={{ p: 2, m: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircleIcon color="success" />
          <Typography variant="h6">{t('providers.libraryofleaks.noHits')}</Typography>
        </Box>
      </Card>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, p: 1 }}>
      <Card sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <WarningAmberIcon color="warning" />
          <Typography variant="h6">
            {t('providers.libraryofleaks.totalHits', {
              count: totalHits,
              collections: collections.length,
            })}
          </Typography>
        </Box>

        <List dense disablePadding>
          {collections.map((c) => (
            <ListItem key={c.url} disableGutters dense>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" fontWeight="bold">{c.label}</Typography>
                    <Chip label={c.category} size="small" variant="outlined" />
                  </Box>
                }
                secondary={
                  <Typography variant="body2" color="text.secondary">
                    {c.count}
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('providers.libraryofleaks.disclaimer')}
        </Typography>

        {searchUrl && (
          <Link
            href={searchUrl} target="_blank" rel="noopener noreferrer"
            sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, mt: 1 }}
          >
            {t('providers.libraryofleaks.viewOnLibraryOfLeaks')}
            <OpenInNewIcon fontSize="inherit" />
          </Link>
        )}
      </Card>
    </Box>
  );
}
