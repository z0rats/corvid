import React from "react";
import { useTranslation } from 'react-i18next';
import { useHackertargetSubdomains } from "../../hooks/api/useHackertargetSubdomains";

import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import DnsIcon from "@mui/icons-material/DnsOutlined";
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

export default function HackertargetPanel({ domain, onScanSubdomain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, unsupported } = useHackertargetSubdomains(domain);

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
        {t('domainFinder.hackertarget.errorPrefix')} {error}
      </Alert>
    );
  }

  if (!data) return null;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.hackertarget.title')}
        </Typography>

        {data.subdomains.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t('domainFinder.hackertarget.noSubdomains')}
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
                title={onScanSubdomain ? t('domainFinder.hackertarget.scanSubdomain') : undefined}
              />
            ))}
          </Stack>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('domainFinder.hackertarget.hostCount', { count: data.total_hosts })}
        </Typography>
      </CardContent>
    </Card>
  );
}
