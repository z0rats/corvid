import React from "react";
import { useTranslation } from 'react-i18next';
import { useRapidDnsSubdomains } from "../../hooks/api/useRapidDnsSubdomains";

import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import DnsIcon from "@mui/icons-material/DnsOutlined";
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

export default function RapidDnsPanel({ domain, onScanSubdomain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, unsupported } = useRapidDnsSubdomains(domain);

  if (unsupported) return null;

  if (loading) {
    return (
      <>
        <LinearProgress />
        <br />
      </>
    );
  }

  if (error) {
    return (
      <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
        {t('domainFinder.rapidDns.errorPrefix')} {error}
      </Alert>
    );
  }

  if (!data) return null;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.rapidDns.title')}
        </Typography>

        {data.subdomains.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t('domainFinder.rapidDns.noSubdomains')}
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
                title={onScanSubdomain ? t('domainFinder.rapidDns.scanSubdomain') : undefined}
              />
            ))}
          </Stack>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('domainFinder.rapidDns.recordCount', { count: data.total_records })}
        </Typography>
      </CardContent>
    </Card>
  );
}
