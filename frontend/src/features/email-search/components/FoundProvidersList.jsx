import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

export default function FoundProvidersList({ providers }) {
  const { t } = useTranslation('emailSearch');

  if (!providers || providers.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t('results.empty')}
      </Typography>
    );
  }

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t('results.foundCount', { count: providers.length })}
      </Typography>
      <List dense>
        {providers.map((provider) => (
          <ListItem key={provider.provider_name}>
            <ListItemIcon sx={{ minWidth: 32 }}>
              <CheckCircleIcon color="success" fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary={provider.provider_name}
              secondary={(provider.emails || []).join(', ')}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}
