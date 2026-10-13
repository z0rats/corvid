import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import Button from '@mui/material/Button';
import ChainActionButton from '../../../core/components/ui/ChainActionButton';

// Google accounts (what GHunt can look up) also sign in with a gmail.com address.
const GOOGLE_EMAIL_DOMAINS = new Set(['gmail.com', 'googlemail.com']);
const isGoogleEmail = (email) => GOOGLE_EMAIL_DOMAINS.has(email.split('@').pop()?.toLowerCase());

// A user_scanner hit carries what the service's profile showed (`extra.fields`) and the service's
// own URL. Image links (`extra.links`) are deliberately not rendered: loading them would contact
// hosts the profile owner controls from the analyst's browser.
function profileSummary(extra) {
  const entries = Object.entries(extra?.fields || {});
  return entries.slice(0, 8).map(([key, value]) => `${key.replace(/_/g, ' ')}: ${value}`).join(' · ');
}

const safeUrl = (url) => (typeof url === 'string' && /^https?:\/\//i.test(url) ? url : null);

/** Checks that failed (blocked, timed out, changed) say nothing about the account. */
export function FailedChecksNote({ count }) {
  const { t } = useTranslation('emailSearch');
  if (!count) return null;
  return (
    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
      {t('scan.errors', { count })}
    </Typography>
  );
}

function EmailActions({ emails, onLookupGoogleProfile }) {
  const { t } = useTranslation('emailSearch');
  if (emails.length === 0) return null;
  return (
    <Stack direction="row" spacing={0.5}>
      {emails.map((email) => (
        <ChainActionButton
          key={email}
          to="/ioc-tools/lookup"
          value={email}
          labelKey="chainActions.sendToIocLookup"
          ns="emailSearch"
        />
      ))}
      {onLookupGoogleProfile && emails.filter(isGoogleEmail).map((email) => (
        <Button key={`ghunt-${email}`} size="small" onClick={() => onLookupGoogleProfile(email)}>
          {t('chainActions.googleProfile')}
        </Button>
      ))}
    </Stack>
  );
}

/**
 * `searchedEmail` is set for a User Scanner run: every hit is the same searched address, so it
 * and its actions are shown once above the list rather than repeated on every row.
 */
export default function FoundProvidersList({ providers, searchedEmail, onLookupGoogleProfile }) {
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
      <Stack direction="row" spacing={1} sx={{ mb: 1, alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="subtitle2">
          {t('results.foundCount', { count: providers.length })}
        </Typography>
        {searchedEmail && (
          <EmailActions emails={[searchedEmail]} onLookupGoogleProfile={onLookupGoogleProfile} />
        )}
      </Stack>
      <List dense>
        {providers.map((provider) => {
          const rowEmails = searchedEmail ? [] : (provider.emails || []);
          return (
            <ListItem key={provider.provider_name}>
              <ListItemIcon sx={{ minWidth: 32 }}>
                <CheckCircleIcon color="success" fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={(
                  <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center' }}>
                    <span>{provider.provider_name}</span>
                    {provider.extra?.category && (
                      <Chip size="small" variant="outlined" label={provider.extra.category} />
                    )}
                    {safeUrl(provider.extra?.url) && (
                      <Link href={safeUrl(provider.extra.url)} target="_blank" rel="noopener noreferrer" variant="caption">
                        {t('results.openService')}
                      </Link>
                    )}
                  </Stack>
                )}
                secondary={[rowEmails.join(', '), profileSummary(provider.extra)].filter(Boolean).join(' — ')}
                slotProps={{ primary: { component: 'div' } }}
              />
              <EmailActions emails={rowEmails} onLookupGoogleProfile={onLookupGoogleProfile} />
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
}
