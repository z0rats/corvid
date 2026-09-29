import React from "react";
import { useTranslation } from 'react-i18next';
import { useDomainPanel } from "../../hooks/useDomainPanel";

import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import DnsIcon from "@mui/icons-material/DnsOutlined";
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';

export default function SubfinderPanel({ domain, onScanSubdomain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, unsupported, run } = useDomainPanel('subfinder-subdomains', domain, { auto: false });

  if (unsupported) return null;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.subfinder.title')}
        </Typography>

        {!data && !loading && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t('domainFinder.subfinder.description')}
            </Typography>
            <Button variant="outlined" startIcon={<TravelExploreIcon />} onClick={run}>
              {t('domainFinder.subfinder.startButton')}
            </Button>
          </>
        )}

        {loading && (
          <>
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="caption" color="text.secondary">
              {t('domainFinder.subfinder.loadingHint')}
            </Typography>
          </>
        )}

        {error && (
          <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mt: 1 }}>
            {t('domainFinder.subfinder.errorPrefix')} {error}
          </Alert>
        )}

        {data && (
          <>
            {data.subdomains.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t('domainFinder.subfinder.noSubdomains')}
              </Typography>
            ) : (
              <Stack direction="row" spacing={1} sx={{ gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <DnsIcon fontSize="small" color="action" />
                {data.subdomains.map((subdomain) => (
                  <Chip
                    key={subdomain}
                    label={subdomain}
                    size="small"
                    variant="outlined"
                    clickable={Boolean(onScanSubdomain)}
                    onClick={onScanSubdomain ? () => onScanSubdomain(subdomain) : undefined}
                    title={onScanSubdomain ? t('domainFinder.subfinder.scanSubdomain') : undefined}
                  />
                ))}
              </Stack>
            )}

            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {t('domainFinder.subfinder.recordCount', { count: data.total_records })}
              </Typography>
              <Button size="small" onClick={run}>
                {t('domainFinder.subfinder.rescanButton')}
              </Button>
            </Stack>
          </>
        )}
      </CardContent>
    </Card>
  );
}
