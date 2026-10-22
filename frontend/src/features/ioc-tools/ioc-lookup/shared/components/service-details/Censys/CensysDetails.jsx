import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import NoDetails from '../NoDetails';
import FieldTable from '../FieldTable';
import { InfoCard, ReservedAddressCard } from '../StatusCard';
import { formatDate, isWaf, softwareLabel } from '../../../utils/detailFormat';

function CertificateTable({ cert, t }) {
  if (!cert) return null;
  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('providers.censys.certificate')}</Typography>
      <FieldTable
        label={t('providers.censys.certificate')}
        rows={[
          { name: t('providers.censys.subject'), value: cert.subject_dn },
          { name: t('providers.censys.issuer'), value: cert.issuer_dn },
          { name: t('providers.censys.names'), value: (cert.names || []).join(', ') },
          {
            name: 'SHA-256',
            value: cert.fingerprint_sha256 && (
              <Box component="span" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                {cert.fingerprint_sha256}
              </Box>
            ),
          },
        ]}
      />
    </Box>
  );
}

function HostView({ result, t }) {
  const services = result.services || [];
  const { autonomous_system: as = {}, location = {} } = result;
  return (
    <>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('providers.censys.servicesHeadline', { count: result.service_count ?? services.length })}
      </Typography>
      <FieldTable
        label={t('providers.censys.hostInfo')}
        rows={[
          { name: t('providers.censys.asn'), value: as.asn ? `AS${as.asn} ${as.name || ''}`.trim() : null },
          { name: t('providers.censys.prefix'), value: as.bgp_prefix },
          { name: t('providers.censys.location'), value: [location.city, location.country].filter(Boolean).join(', ') },
          { name: t('providers.censys.hostnames'), value: (result.hostnames || []).join(', ') },
        ]}
      />
      {services.length > 0 && (
        <Table size="small" aria-label={t('providers.censys.servicesTable')} sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>{t('providers.censys.port')}</TableCell>
              <TableCell>{t('providers.censys.protocol')}</TableCell>
              <TableCell>{t('providers.censys.transport')}</TableCell>
              <TableCell>{t('providers.censys.certificate')}</TableCell>
              <TableCell>{t('providers.censys.lastScan')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {services.map((service, index) => (
              <TableRow key={index}>
                <TableCell>{service.port}</TableCell>
                <TableCell>{service.protocol}</TableCell>
                <TableCell>{service.transport_protocol}</TableCell>
                <TableCell>{service.cert?.subject_dn || ''}</TableCell>
                <TableCell>{formatDate(service.scan_time)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  );
}

function WebPropertyView({ result, t }) {
  const software = result.software || [];
  return (
    <>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('providers.censys.webpropertyHeadline', { hostname: result.hostname, port: result.port })}
      </Typography>
      {software.length > 0 ? (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
          {/* Index keys: Censys can report the same product twice. */}
          {software.map((item, index) => {
            const waf = isWaf(item);
            const label = softwareLabel(item);
            return (
              <Chip
                key={index}
                label={waf ? `${label} · ${t('providers.censys.waf')}` : label}
                size="small"
                variant="outlined"
                color={waf ? 'warning' : 'default'}
              />
            );
          })}
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary">{t('providers.censys.noSoftware')}</Typography>
      )}
      {result.scan_time && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {t('providers.censys.lastScan')}: {formatDate(result.scan_time)}
        </Typography>
      )}
      <CertificateTable cert={result.cert} t={t} />
    </>
  );
}

export default function CensysDetails({ result }) {
  const { t } = useTranslation('iocTools');

  if (!result) {
    return <NoDetails message={t('providers.censys.unavailable')} />;
  }
  if (result.reserved) {
    return <ReservedAddressCard />;
  }
  if (result.not_found) {
    return <InfoCard title={t('providers.censys.notFound')} />;
  }

  return (
    <Card sx={{ p: 2, m: 1 }}>
      {result.kind === 'webproperty' ? <WebPropertyView result={result} t={t} /> : <HostView result={result} t={t} />}
    </Card>
  );
}
