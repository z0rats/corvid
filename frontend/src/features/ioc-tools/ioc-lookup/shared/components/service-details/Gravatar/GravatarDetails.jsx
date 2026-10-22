import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import { buildPrefillUrl } from '../../../../../../../core/utils/crossFeatureNav';
import NoDetails from '../NoDetails';
import FieldTable from '../FieldTable';
import { InfoCard } from '../StatusCard';

// Gravatar `service_type` -> the Corvid feature that takes that account as `?q=`. Steam
// Recon takes the profile URL; the others take the username. Every account also gets a
// generic username search.
const ACCOUNT_PIVOTS = {
  github: { path: '/git-recon', labelKey: 'gitRecon' },
  reddit: { path: '/reddit-search', labelKey: 'redditSearch' },
  instagram: { path: '/instagram-search', labelKey: 'instagramSearch' },
  steam: { path: '/steam-recon', labelKey: 'steamRecon', useUrl: true },
};

function ExternalLink({ href, children }) {
  return (
    <Link href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </Link>
  );
}

function AccountPivots({ account, t, navigate }) {
  const pivot = ACCOUNT_PIVOTS[account.service];
  const go = (path, value) => navigate(buildPrefillUrl(path, value));
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
      {pivot && (pivot.useUrl ? account.url : account.username) && (
        <Chip
          size="small"
          clickable
          color="primary"
          variant="outlined"
          label={t(`providers.gravatar.pivots.${pivot.labelKey}`)}
          onClick={() => go(pivot.path, pivot.useUrl ? account.url : account.username)}
        />
      )}
      {account.username && (
        <Chip
          size="small"
          clickable
          variant="outlined"
          label={t('providers.gravatar.pivots.usernameSearch')}
          onClick={() => go('/username-search', account.username)}
        />
      )}
    </Box>
  );
}

export default function GravatarDetails({ result }) {
  const { t } = useTranslation('iocTools');
  const navigate = useNavigate();

  if (!result) {
    return <NoDetails message={t('providers.gravatar.unavailable')} />;
  }
  if (!result.found) {
    return <InfoCard title={t('providers.gravatar.notFound')} />;
  }

  const accounts = result.verified_accounts || [];

  return (
    <Card sx={{ p: 2, m: 1 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {result.display_name || t('providers.gravatar.unnamed')}
      </Typography>
      <FieldTable
        label={t('providers.gravatar.profile')}
        rows={[
          { name: t('providers.gravatar.jobTitle'), value: result.job_title },
          { name: t('providers.gravatar.company'), value: result.company },
          { name: t('providers.gravatar.location'), value: result.location },
          { name: t('providers.gravatar.about'), value: result.description },
          {
            name: t('providers.gravatar.profileUrl'),
            value: result.profile_url && <ExternalLink href={result.profile_url}>{result.profile_url}</ExternalLink>,
          },
          {
            // A link, never an <img>: rendering it would have the analyst's browser fetch from
            // Gravatar on its own and tell Gravatar the profile was looked at.
            // `has_avatar: false` means the URL only serves Gravatar's default image.
            name: t('providers.gravatar.avatar'),
            value: result.has_avatar === false
              ? t('providers.gravatar.defaultAvatar')
              : result.avatar_url && (
                <ExternalLink href={result.avatar_url}>{t('providers.gravatar.openAvatar')}</ExternalLink>
              ),
          },
        ]}
      />

      <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
        {t('providers.gravatar.verifiedAccounts', { count: accounts.length })}
      </Typography>
      {accounts.length > 0 && (
        <Table size="small" aria-label={t('providers.gravatar.verifiedAccountsTable')}>
          <TableHead>
            <TableRow>
              <TableCell>{t('providers.gravatar.service')}</TableCell>
              <TableCell>{t('providers.gravatar.account')}</TableCell>
              <TableCell>{t('providers.gravatar.pivot')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {accounts.map((account) => (
              <TableRow key={account.url || `${account.service}-${account.username}`}>
                <TableCell>{account.label || account.service}</TableCell>
                <TableCell>
                  {account.url ? (
                    <ExternalLink href={account.url}>{account.username || account.url}</ExternalLink>
                  ) : account.username}
                </TableCell>
                <TableCell><AccountPivots account={account} t={t} navigate={navigate} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        {t('providers.gravatar.disclaimer')}
      </Typography>
    </Card>
  );
}
