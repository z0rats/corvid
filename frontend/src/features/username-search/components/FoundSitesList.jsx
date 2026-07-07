import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Link from '@mui/material/Link';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

export default function FoundSitesList({ sites }) {
  const { t } = useTranslation('usernameSearch');

  if (!sites || sites.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t('results.empty')}
      </Typography>
    );
  }

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t('results.foundCount', { count: sites.length })}
      </Typography>
      <List dense>
        {sites.map((site) => (
          <ListItem key={`${site.site_name}-${site.url_user}`}>
            <ListItemIcon sx={{ minWidth: 32 }}>
              <CheckCircleIcon color="success" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary={site.extra?.title || site.site_name}
              secondary={
                <Link href={site.url_user} target="_blank" rel="noopener noreferrer">
                  {site.url_user}
                </Link>
              }
            />
            {site.extra?.rate && (
              <Typography variant="caption" color="text.secondary">{site.extra.rate}</Typography>
            )}
          </ListItem>
        ))}
      </List>
    </Box>
  );
}
