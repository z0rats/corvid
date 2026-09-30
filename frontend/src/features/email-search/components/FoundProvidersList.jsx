import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import Button from '@mui/material/Button';
import ChainActionButton from '../../../core/components/ui/ChainActionButton';

// Google accounts (what GHunt can look up) also sign in with a gmail.com address.
const GOOGLE_EMAIL_DOMAINS = new Set(['gmail.com', 'googlemail.com']);
const isGoogleEmail = (email) => GOOGLE_EMAIL_DOMAINS.has(email.split('@').pop()?.toLowerCase());

export default function FoundProvidersList({ providers, onLookupGoogleProfile }) {
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
            {(provider.emails || []).length > 0 && (
              <Stack direction="row" spacing={0.5}>
                {provider.emails.map((email) => (
                  <ChainActionButton
                    key={email}
                    to="/ioc-tools/lookup"
                    value={email}
                    labelKey="chainActions.sendToIocLookup"
                    ns="emailSearch"
                  />
                ))}
                {onLookupGoogleProfile && provider.emails.filter(isGoogleEmail).map((email) => (
                  <Button key={`ghunt-${email}`} size="small" onClick={() => onLookupGoogleProfile(email)}>
                    {t('chainActions.googleProfile')}
                  </Button>
                ))}
              </Stack>
            )}
          </ListItem>
        ))}
      </List>
    </Box>
  );
}
