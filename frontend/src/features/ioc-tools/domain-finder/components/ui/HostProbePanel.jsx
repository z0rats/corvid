import React from "react";
import { useTranslation } from 'react-i18next';
import { useHostProbe } from "../../hooks/api/useHostProbe";

import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';

function HostResult({ t, result }) {
  return (
    <Stack spacing={0.5} sx={{ py: 1 }}>
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
        <Chip size="small" label={result.scheme} color={result.scheme === 'https' ? 'success' : 'default'} />
        <Chip size="small" label={result.status_code} variant="outlined" />
        {result.webserver && <Chip size="small" label={result.webserver} variant="outlined" />}
        {result.technologies.map((tech) => (
          <Chip key={tech} size="small" label={tech} variant="outlined" />
        ))}
      </Stack>
      {result.title && (
        <Typography variant="body2">{result.title}</Typography>
      )}
      {result.final_url && result.final_url !== result.url && (
        <Typography variant="caption" color="text.secondary">
          {t('domainFinder.hostProbe.redirectsTo')} {result.final_url}
        </Typography>
      )}
      {result.favicon_hash && (
        <Typography variant="caption" color="text.secondary">
          {t('domainFinder.hostProbe.faviconHash')} {result.favicon_hash}
        </Typography>
      )}
      {result.tls && (
        <Typography variant="caption" color="text.secondary">
          {t('domainFinder.hostProbe.tlsIssuer')} {result.tls.issuer_cn || result.tls.issuer_dn || '—'}
        </Typography>
      )}
    </Stack>
  );
}

export default function HostProbePanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, unsupported, run } = useHostProbe(domain);

  if (unsupported) return null;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.hostProbe.title')}
        </Typography>

        {!data && !loading && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t('domainFinder.hostProbe.description')}
            </Typography>
            <Button variant="outlined" startIcon={<TravelExploreIcon />} onClick={run}>
              {t('domainFinder.hostProbe.startButton')}
            </Button>
          </>
        )}

        {loading && <LinearProgress sx={{ mb: 1 }} />}

        {error && (
          <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mt: 1 }}>
            {t('domainFinder.hostProbe.errorPrefix')} {error}
          </Alert>
        )}

        {data && (
          <Stack spacing={0.5}>
            {!data.reachable ? (
              <Typography variant="body2" color="text.secondary">
                {t('domainFinder.hostProbe.notReachable')}
              </Typography>
            ) : (
              data.results.map((result, index) => (
                <React.Fragment key={result.url}>
                  {index > 0 && <Divider />}
                  <HostResult t={t} result={result} />
                </React.Fragment>
              ))
            )}

            <Button size="small" onClick={run} sx={{ alignSelf: 'flex-start' }}>
              {t('domainFinder.hostProbe.rescanButton')}
            </Button>
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
