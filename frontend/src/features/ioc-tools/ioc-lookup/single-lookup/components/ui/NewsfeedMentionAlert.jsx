import React from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Box from '@mui/material/Box';

function NewsfeedMentionAlert({ mentions }) {
  const { t } = useTranslation('iocTools');

  if (!mentions || mentions.length === 0) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Alert severity="warning" variant="outlined">
        <AlertTitle>{t('singleLookup.newsfeedMentions.title')}</AlertTitle>
        {t('singleLookup.newsfeedMentions.message', { count: mentions.length })}
        <List dense disablePadding>
          {mentions.map((mention) => (
            <ListItem key={mention.article_id} disableGutters sx={{ py: 0.25 }}>
              <ListItemText
                primary={
                  <Link href={mention.link} target="_blank" rel="noopener noreferrer">
                    {mention.title}
                  </Link>
                }
                secondary={`${mention.feedname} — ${new Date(mention.date).toLocaleString()}`}
              />
            </ListItem>
          ))}
        </List>
      </Alert>
    </Box>
  );
}

export default NewsfeedMentionAlert;
