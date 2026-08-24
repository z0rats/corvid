import React from "react";
import { useTranslation } from 'react-i18next';
import { useWebCheck } from "../../hooks/api/useWebCheck";
import { domainUtils } from "../../utils/domainUtils";

import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

function Section({ title, loading, error, errorPrefix, children }) {
  return (
    <Stack spacing={1} sx={{ py: 1 }}>
      <Typography variant="subtitle2">{title}</Typography>
      {loading && <LinearProgress />}
      {error && (
        <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1 }}>
          {errorPrefix} {error}
        </Alert>
      )}
      {!loading && !error && children}
    </Stack>
  );
}

function SslSection({ t, check }) {
  const { data } = check;
  if (!data) return null;
  return (
    <Stack spacing={0.5}>
      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
        <Chip
          size="small"
          label={
            data.is_expired
              ? t('domainFinder.webCheck.ssl.expired')
              : t('domainFinder.webCheck.ssl.valid', { days: data.days_until_expiry })
          }
          color={data.is_expired ? 'error' : 'success'}
          variant="outlined"
        />
        <Chip
          size="small"
          label={
            data.hostname_matches
              ? t('domainFinder.webCheck.ssl.hostnameMatches')
              : t('domainFinder.webCheck.ssl.hostnameMismatch')
          }
          color={data.hostname_matches ? 'success' : 'error'}
          variant="outlined"
        />
        {data.tls_version && <Chip size="small" label={data.tls_version} variant="outlined" />}
      </Stack>
      <Typography variant="body2" color="text.secondary">
        {t('domainFinder.webCheck.ssl.issuer')} {data.issuer}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {t('domainFinder.webCheck.ssl.subject')} {data.subject}
      </Typography>
    </Stack>
  );
}

function HeadersSection({ t, check }) {
  const { data } = check;
  if (!data) return null;
  const presentEntries = Object.entries(data.present_headers || {});
  return (
    <Stack spacing={0.5}>
      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
        {presentEntries.map(([label]) => (
          <Chip key={label} size="small" label={label} color="success" variant="outlined" />
        ))}
        {(data.missing_headers || []).map((label) => (
          <Chip key={label} size="small" label={label} variant="outlined" />
        ))}
      </Stack>
      <Typography variant="caption" color="text.secondary">
        {t('domainFinder.webCheck.headers.summary', {
          present: presentEntries.length,
          missing: (data.missing_headers || []).length
        })}
      </Typography>
      {data.hsts && (
        <Typography variant="caption" color="text.secondary">
          {t('domainFinder.webCheck.headers.hstsMaxAge', { maxAge: data.hsts.max_age })}
          {data.hsts.include_subdomains ? ` · ${t('domainFinder.webCheck.headers.includeSubdomains')}` : ''}
          {data.hsts.preload ? ` · ${t('domainFinder.webCheck.headers.preload')}` : ''}
        </Typography>
      )}
    </Stack>
  );
}

function DnssecSection({ t, check }) {
  const { data } = check;
  if (!data) return null;
  return (
    <Chip
      size="small"
      label={
        data.dnssec_enabled
          ? t('domainFinder.webCheck.dnssec.enabled')
          : t('domainFinder.webCheck.dnssec.disabled')
      }
      color={data.dnssec_enabled ? 'success' : 'default'}
      variant="outlined"
    />
  );
}

function BlocklistSection({ t, check }) {
  const { data } = check;
  if (!data) return null;
  return (
    <Stack spacing={0.5}>
      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
        {(data.results || []).map((r) => (
          <Chip
            key={r.provider}
            size="small"
            label={r.provider}
            color={r.blocked ? 'error' : 'success'}
            variant="outlined"
          />
        ))}
      </Stack>
      <Typography variant="caption" color="text.secondary">
        {t('domainFinder.webCheck.blocklist.summary', { count: data.flagged_count })}
      </Typography>
    </Stack>
  );
}

export default function WebCheckPanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const { ssl, headers, dnssec, blocklist, unsupported } = useWebCheck(domain);

  if (unsupported) return null;
  if (!domain) return null;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.webCheck.title')}
        </Typography>

        <Section
          title={t('domainFinder.webCheck.ssl.title')}
          loading={ssl.loading}
          error={ssl.error}
          errorPrefix={t('domainFinder.webCheck.ssl.errorPrefix')}
        >
          <SslSection t={t} check={ssl} />
        </Section>

        <Divider />

        <Section
          title={t('domainFinder.webCheck.headers.title')}
          loading={headers.loading}
          error={headers.error}
          errorPrefix={t('domainFinder.webCheck.headers.errorPrefix')}
        >
          <HeadersSection t={t} check={headers} />
        </Section>

        <Divider />

        <Section
          title={t('domainFinder.webCheck.dnssec.title')}
          loading={dnssec.loading}
          error={dnssec.error}
          errorPrefix={t('domainFinder.webCheck.dnssec.errorPrefix')}
        >
          <DnssecSection t={t} check={dnssec} />
        </Section>

        <Divider />

        <Section
          title={t('domainFinder.webCheck.blocklist.title')}
          loading={blocklist.loading}
          error={blocklist.error}
          errorPrefix={t('domainFinder.webCheck.blocklist.errorPrefix')}
        >
          <BlocklistSection t={t} check={blocklist} />
        </Section>

        {ssl.data && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {t('domainFinder.webCheck.checkedAt')} {domainUtils.formatDate(ssl.data.timestamp)}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
