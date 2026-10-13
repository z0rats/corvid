import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { EMPTY_PIVOTS, guessEmails } from '../utils/discoveredIdentifiers';
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
 * Pivot suggestions after a scan: handles, names and emails the backend harvested from the found
 * profiles (`pivots`), username guesses derived from those names, and candidate email addresses
 * for the searched handle. All hypotheses - the same handle is often a different person.
 */
// Stored with the run as its provenance label (deliberately not translated). Built from profile
// text, so capped to the backend's 200-character limit - an over-long label would fail the request.
const MAX_SOURCE_LENGTH = 200;
const label = (text) => text.slice(0, MAX_SOURCE_LENGTH);
const handleSource = ({ kind, sites }) => label(`${kind === 'link' ? 'link on' : 'reported by'} ${sites.join(', ')}`);

export default function DiscoveredIdentifiers({ pivots, username, onSearchUsername, onCheckSite, disabled }) {
  const { t } = useTranslation('usernameSearch');
  const navigate = useNavigate();

  const { usernames, names, emails: publishedEmails } = pivots ?? EMPTY_PIVOTS;
  const handles = useMemo(() => usernames.filter((u) => u.searchable), [usernames]);
  const platformIds = useMemo(() => usernames.filter((u) => !u.searchable), [usernames]);
  const nameVariants = useMemo(() => {
    const known = new Set([username.toLowerCase(), ...handles.map((u) => u.value.toLowerCase())]);
    return names.map((name) => ({
      name: name.value,
      variants: generateUsernameVariants(name.value)
        .filter(({ value }) => !known.has(value))
        .slice(0, NAME_VARIANTS_PER_NAME),
    })).filter(({ variants }) => variants.length > 0);
  }, [names, handles, username]);
  const emailGuesses = useMemo(() => guessEmails(username), [username]);

  if (usernames.length === 0 && names.length === 0 && publishedEmails.length === 0 && emailGuesses.length === 0) {
    return null;
  }

  const usernameChip = (value, tooltip, pivotSource) => (
    <Tooltip key={value} title={tooltip}>
      <Chip
        size="small"
        variant="outlined"
        color="primary"
        label={value}
        onClick={() => onSearchUsername(value, { pivotSource })}
        disabled={disabled}
      />
    </Tooltip>
  );

  // A handle seen in a profile link already names its site, so one request can confirm it.
  const checkSiteButton = (handle) => (onCheckSite && handle.site ? (
    <Button
      key={`check-${handle.value}`}
      size="small"
      disabled={disabled}
      onClick={() => onCheckSite(handle, { pivotSource: handleSource(handle) })}
    >
      {t('discovered.checkOnSite', { site: handle.site })}
    </Button>
  ) : null);

  const handleTooltip = ({ kind, site, sites }) => (kind === 'link'
    ? t('discovered.linkSource', { site, sites: sites.join(', ') })
    : t('discovered.reportedSource', { sites: sites.join(', ') }));

  return (
    <Box sx={{ mt: 2, mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 0.5 }}>{t('discovered.title')}</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
        {t('discovered.caveat')}
      </Typography>

      {handles.length > 0 && (
        <Section title={t('discovered.usernames')} hint={t('discovered.clickToSearch')}>
          {handles.map((handle) => (
            <Stack key={handle.value} direction="row" sx={{ alignItems: 'center' }}>
              {usernameChip(handle.value, handleTooltip(handle), handleSource(handle))}
              {checkSiteButton(handle)}
            </Stack>
          ))}
        </Section>
      )}

      {platformIds.length > 0 && (
        <Section title={t('discovered.platformIds')} hint={t('discovered.platformIdsHint')}>
          {platformIds.map(({ value, id_type: idType, sites }) => (
            <Tooltip key={value} title={t('discovered.usernameSource', { type: idType, sites: sites.join(', ') })}>
              <Chip size="small" variant="outlined" label={`${value} (${idType})`} />
            </Tooltip>
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
          {variants.map(({ value, reason }) => (
            usernameChip(value, t(`form.variantReason.${reason}`), label(`name guess from "${name}"`))
          ))}
        </Section>
      ))}

      {publishedEmails.length > 0 && (
        <Section title={t('discovered.publishedEmails')} hint={t('discovered.emailsHint')}>
          {publishedEmails.map(({ value, sites: from }) => (
            <Tooltip key={value} title={t('discovered.reportedSource', { sites: from.join(', ') })}>
              <Chip
                size="small"
                variant="outlined"
                color="primary"
                label={value}
                onClick={() => navigate(buildPrefillUrl('/ioc-tools/lookup', value))}
              />
            </Tooltip>
          ))}
        </Section>
      )}

      {emailGuesses.length > 0 && (
        <Section title={t('discovered.emails', { username })} hint={t('discovered.emailsHint')}>
          {emailGuesses.map((email) => (
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
