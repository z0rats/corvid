import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import WarningIcon from '@mui/icons-material/Warning';
import NoDetails from '../NoDetails';

// The host response caps its `urls` list at 100 entries; showing them all buries the summary.
const MAX_LISTED_URLS = 10;

const STATUS_COLOR = { online: 'error', offline: 'warning', unknown: 'default' };

const centered = { margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 };

function StatusChip({ status }) {
  return <Chip size="small" label={status} color={STATUS_COLOR[status] || 'default'} />;
}

function Field({ label, value }) {
  if (value === null || value === undefined || value === '' || value === false) return null;
  return (
    <ListItem disableGutters sx={{ py: 0.25 }}>
      <ListItemText
        primary={label}
        secondary={value}
        primaryTypographyProps={{ variant: 'caption', color: 'text.secondary' }}
        secondaryTypographyProps={{ variant: 'body2', component: 'div', sx: { wordBreak: 'break-all' } }}
      />
    </ListItem>
  );
}

function TagChips({ tags }) {
  if (!tags?.length) return null;
  return (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
      {tags.map((tag) => <Chip key={tag} label={tag} size="small" variant="outlined" />)}
    </Box>
  );
}

function Blacklists({ blacklists }) {
  const { t } = useTranslation('iocTools');
  const entries = Object.entries(blacklists || {});
  if (entries.length === 0) return null;
  return (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
      {entries.map(([name, status]) => (
        <Chip
          key={name}
          size="small"
          variant="outlined"
          color={status === 'not listed' ? 'default' : 'error'}
          label={t('providers.urlhaus.blacklistEntry', { name, status: status.replace(/_/g, ' ') })}
        />
      ))}
    </Box>
  );
}

function PayloadList({ payloads }) {
  const { t } = useTranslation('iocTools');
  if (!payloads?.length) return null;
  return (
    <>
      <Divider sx={{ my: 1 }} />
      <Typography variant="subtitle2">{t('providers.urlhaus.payloads', { count: payloads.length })}</Typography>
      <List dense disablePadding>
        {payloads.map((payload) => (
          <ListItem key={payload.response_sha256} disableGutters>
            <ListItemText
              primary={[payload.filename, payload.file_type, payload.signature].filter(Boolean).join(' · ')}
              secondary={payload.response_sha256}
              secondaryTypographyProps={{ sx: { wordBreak: 'break-all' } }}
            />
          </ListItem>
        ))}
      </List>
    </>
  );
}

function UrlEntryList({ urls }) {
  const { t } = useTranslation('iocTools');
  return (
    <>
      <Divider sx={{ my: 1 }} />
      <Typography variant="subtitle2">{t('providers.urlhaus.urlsOnHost')}</Typography>
      <List dense disablePadding>
        {urls.slice(0, MAX_LISTED_URLS).map((entry) => (
          <ListItem key={entry.id || entry.url} disableGutters sx={{ display: 'block' }}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <StatusChip status={entry.url_status} />
              <Link href={entry.urlhaus_reference} target="_blank" rel="noopener noreferrer" sx={{ wordBreak: 'break-all' }}>
                {entry.url}
              </Link>
            </Box>
            <TagChips tags={entry.tags} />
          </ListItem>
        ))}
      </List>
      {urls.length > MAX_LISTED_URLS && (
        <Typography variant="caption" color="text.secondary">
          {t('providers.urlhaus.moreUrls', { count: urls.length - MAX_LISTED_URLS })}
        </Typography>
      )}
    </>
  );
}

export default function UrlHausDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');

  if (!result || result.error) {
    const message = result?.error
      ? t('providers.urlhaus.errorFetching', { error: result.message || result.error })
      : t('providers.urlhaus.unavailable');
    return (
      <Box sx={centered}>
        <NoDetails message={message} />
      </Box>
    );
  }

  if (result.query_status === 'no_results') {
    return (
      <Box sx={{ ...centered, flexDirection: 'column', textAlign: 'center' }}>
        <CheckCircleOutlineIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
        <Typography variant="h6">{t('providers.urlhaus.notFound', { ioc })}</Typography>
      </Box>
    );
  }

  if (result.query_status !== 'ok') {
    return (
      <Box sx={centered}>
        <NoDetails message={t('providers.urlhaus.queryStatus', { status: (result.query_status || '').replace(/_/g, ' ') })} />
      </Box>
    );
  }

  // /v1/host/ answers with a `urls` list, /v1/url/ with the single URL's own fields.
  const isHostResult = Array.isArray(result.urls);
  const hasBlacklists = Object.keys(result.blacklists || {}).length > 0;

  return (
    <Card elevation={0} sx={{ m: 1, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <WarningIcon color="error" />
          <Typography variant="h6" component="h2" sx={{ wordBreak: 'break-all' }}>
            {isHostResult
              ? t('providers.urlhaus.hostTitle', { host: result.host || ioc })
              : t('providers.urlhaus.urlTitle')}
          </Typography>
          {!isHostResult && <StatusChip status={result.url_status} />}
        </Box>

        <List dense disablePadding>
          <Field label={t('providers.urlhaus.threat')} value={result.threat?.replace(/_/g, ' ')} />
          <Field label={t('providers.urlhaus.host')} value={isHostResult ? null : result.host} />
          <Field label={t('providers.urlhaus.firstSeen')} value={result.firstseen || result.date_added} />
          <Field label={t('providers.urlhaus.lastOnline')} value={result.last_online} />
          <Field label={t('providers.urlhaus.urlCount')} value={result.url_count} />
          <Field label={t('providers.urlhaus.reporter')} value={result.reporter} />
          <Field label={t('providers.urlhaus.blacklists')} value={hasBlacklists && <Blacklists blacklists={result.blacklists} />} />
          <Field label={t('providers.urlhaus.tags')} value={result.tags?.length > 0 && <TagChips tags={result.tags} />} />
        </List>

        {isHostResult ? <UrlEntryList urls={result.urls} /> : <PayloadList payloads={result.payloads} />}

        {result.urlhaus_reference && (
          <Box sx={{ mt: 1 }}>
            <Link href={result.urlhaus_reference} target="_blank" rel="noopener noreferrer">
              {t('providers.urlhaus.viewOnUrlhaus')}
            </Link>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
