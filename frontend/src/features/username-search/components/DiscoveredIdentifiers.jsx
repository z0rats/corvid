import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { aggregateDiscovered, guessEmails } from '../utils/discoveredIdentifiers';
import { generateUsernameVariants } from '../utils/usernameVariants';
import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';

const NAME_VARIANTS_PER_NAME = 6;

function Section({ title, hint, children }) {
  return (
    <Box sx={{ mb: 1.5 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
        {title}{hint ? ` — ${hint}` : ''}
      </Typography>
      <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 0.75, alignItems: 'center' }}>{children}</Stack>
    </Box>
  );
}

/**
 * Pivot suggestions after a scan: handles/names Maigret parsed out of found profiles, username
 * guesses derived from those names, and candidate email addresses for the searched handle.
 * All hypotheses - the same handle is often a different person.
 */
export default function DiscoveredIdentifiers({ sites, username, onSearchUsername, disabled }) {
  const { t } = useTranslation('usernameSearch');
  const navigate = useNavigate();

  const { usernames, names } = useMemo(() => aggregateDiscovered(sites, username), [sites, username]);
  const nameVariants = useMemo(() => {
    const known = new Set([username.toLowerCase(), ...usernames.map((u) => u.value.toLowerCase())]);
    return names.map((name) => ({
      name: name.value,
      variants: generateUsernameVariants(name.value)
        .filter(({ value }) => !known.has(value))
        .slice(0, NAME_VARIANTS_PER_NAME),
    })).filter(({ variants }) => variants.length > 0);
  }, [names, usernames, username]);
  const emails = useMemo(() => guessEmails(username), [username]);

  if (usernames.length === 0 && names.length === 0 && emails.length === 0) return null;

  const usernameChip = (value, tooltip) => (
    <Tooltip key={value} title={tooltip}>
      <Chip
        size="small"
        variant="outlined"
        color="primary"
        label={value}
        onClick={() => onSearchUsername(value)}
        disabled={disabled}
      />
    </Tooltip>
  );

  return (
    <Box sx={{ mt: 2, mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>{t('discovered.title')}</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
        {t('discovered.caveat')}
      </Typography>

      {usernames.length > 0 && (
        <Section title={t('discovered.usernames')} hint={t('discovered.clickToSearch')}>
          {usernames.map(({ value, type, sites: from }) => usernameChip(
            value,
            t('discovered.usernameSource', { type, sites: from.join(', ') }),
          ))}
        </Section>
      )}

      {names.length > 0 && (
        <Section title={t('discovered.names')}>
          {names.map(({ value, sites: from }) => (
            <Tooltip key={value} title={from.join(', ')}>
              <Chip size="small" label={value} />
            </Tooltip>
          ))}
        </Section>
      )}

      {nameVariants.map(({ name, variants }) => (
        <Section key={name} title={t('discovered.fromName', { name })} hint={t('discovered.clickToSearch')}>
          {variants.map(({ value, reason }) => usernameChip(value, t(`form.variantReason.${reason}`)))}
        </Section>
      ))}

      {emails.length > 0 && (
        <Section title={t('discovered.emails', { username })} hint={t('discovered.emailsHint')}>
          {emails.map((email) => (
            <Chip
              key={email}
              size="small"
              variant="outlined"
              label={email}
              onClick={() => navigate(buildPrefillUrl('/ioc-tools/lookup', email))}
            />
          ))}
          <Button
            size="small"
            onClick={() => navigate(buildPrefillUrl('/email-search/new', username))}
          >
            {t('discovered.checkProviders')}
          </Button>
        </Section>
      )}
    </Box>
  );
}
