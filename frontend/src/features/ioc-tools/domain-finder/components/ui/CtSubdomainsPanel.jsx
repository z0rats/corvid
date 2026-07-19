import React from "react";
import { useTranslation } from 'react-i18next';
import { useCtSubdomains } from "../../hooks/api/useCtSubdomains";

import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import DnsIcon from "@mui/icons-material/DnsOutlined";
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

export default function CtSubdomainsPanel({ domain, onScanSubdomain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, unsupported } = useCtSubdomains(domain);

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
        {t('domainFinder.ctSubdomains.errorPrefix')} {error}
      </Alert>
    );
  }

  if (!data) return null;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.ctSubdomains.title')}
        </Typography>

        {data.subdomains.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t('domainFinder.ctSubdomains.noSubdomains')}
          </Typography>
        ) : (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ gap: 1 }}>
            <DnsIcon fontSize="small" color="action" />
            {data.subdomains.map((subdomain) => (
              <Chip
                key={subdomain}
                label={subdomain}
                size="small"
                variant="outlined"
                clickable={Boolean(onScanSubdomain)}
                onClick={onScanSubdomain ? () => onScanSubdomain(subdomain) : undefined}
                title={onScanSubdomain ? t('domainFinder.ctSubdomains.scanSubdomain') : undefined}
              />
            ))}
          </Stack>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('domainFinder.ctSubdomains.certificateCount', { count: data.total_certificates })}
        </Typography>
      </CardContent>
    </Card>
  );
}
