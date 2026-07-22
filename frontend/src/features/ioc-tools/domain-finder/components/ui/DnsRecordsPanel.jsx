import React from "react";
import { useTranslation } from 'react-i18next';
import { useDnsLookup } from "../../hooks/api/useDnsLookup";

import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import DnsIcon from "@mui/icons-material/DnsOutlined";
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

const RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"];

export default function DnsRecordsPanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, unsupported } = useDnsLookup(domain);

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
        {t('domainFinder.dnsRecords.errorPrefix')} {error}
      </Alert>
    );
  }

  if (!data) return null;

  const recordTypesWithData = RECORD_TYPES.filter((type) => data.records[type]?.length > 0);
  const reverseEntries = Object.entries(data.reverse_dns || {});

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.dnsRecords.title')}
        </Typography>

        {recordTypesWithData.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t('domainFinder.dnsRecords.noRecords')}
          </Typography>
        ) : (
          <Stack spacing={1}>
            {recordTypesWithData.map((type) => (
              <Stack key={type} direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ gap: 1 }}>
                <Chip label={type} size="small" color="primary" variant="filled" sx={{ minWidth: 64 }} />
                {data.records[type].map((value) => (
                  <Chip key={`${type}_${value}`} label={value} size="small" variant="outlined" />
                ))}
              </Stack>
            ))}
          </Stack>
        )}

        {reverseEntries.length > 0 && (
          <>
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              {t('domainFinder.dnsRecords.reverseDnsTitle')}
            </Typography>
            <Stack spacing={1}>
              {reverseEntries.map(([ip, hosts]) => (
                <Stack key={ip} direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ gap: 1 }}>
                  <DnsIcon fontSize="small" color="action" />
                  <Chip label={ip} size="small" variant="filled" />
                  {hosts.map((host) => (
                    <Chip key={`${ip}_${host}`} label={host} size="small" variant="outlined" />
                  ))}
                </Stack>
              ))}
            </Stack>
          </>
        )}
      </CardContent>
    </Card>
  );
}
