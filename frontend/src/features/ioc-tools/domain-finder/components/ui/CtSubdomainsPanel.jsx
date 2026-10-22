import React from "react";
import { useTranslation } from 'react-i18next';
import { useDomainPanel } from "../../hooks/useDomainPanel";
import { panelStatusView } from "./panelStatusView";

import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import DnsIcon from "@mui/icons-material/DnsOutlined";
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

// One line per CT source: what it found, or that it was not checked - a failed source is
// never read as "no subdomains".
function sourceLine(t, source) {
  if (!source.ok) {
    return t('domainFinder.ctSubdomains.sourceFailed', {
      name: source.name,
      error: source.error,
      code: source.error_code,
    });
  }
  const key = source.truncated ? 'sourceTruncated' : 'sourceOk';
  return t(`domainFinder.ctSubdomains.${key}`, {
    name: source.name,
    count: source.subdomain_count,
    certificates: source.certificate_count,
  });
}

export default function CtSubdomainsPanel({ domain, onScanSubdomain }) {
  const { t } = useTranslation('iocTools');
  const panel = useDomainPanel('ct-subdomains', domain);
  const { data } = panel;

  const status = panelStatusView(panel, t('domainFinder.ctSubdomains.errorPrefix'));
  if (status !== undefined) return status;

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
                title={onScanSubdomain ? t('domainFinder.ctSubdomains.scanSubdomain') : undefined}
              />
            ))}
          </Stack>
        )}

        {(data.sources ?? []).map((source) => (
          <Typography
            key={source.name}
            variant="caption"
            color={source.ok ? 'text.secondary' : 'warning.main'}
            sx={{ display: 'block', mt: 1 }}
          >
            {sourceLine(t, source)}
          </Typography>
        ))}
      </CardContent>
    </Card>
  );
}
