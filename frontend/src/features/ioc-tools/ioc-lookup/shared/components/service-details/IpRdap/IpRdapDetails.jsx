import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import { buildPrefillUrl } from '../../../../../../../core/utils/crossFeatureNav';
import NoDetails from '../NoDetails';
import FieldTable from '../FieldTable';
import { InfoCard, ReservedAddressCard } from '../StatusCard';
import { formatDate } from '../../../utils/detailFormat';

export default function IpRdapDetails({ result }) {
  const { t } = useTranslation('iocTools');
  const navigate = useNavigate();

  if (!result) {
    return <NoDetails message={t('providers.ipRdap.unavailable')} />;
  }
  if (result.reserved) {
    return <ReservedAddressCard />;
  }
  if (!result.found) {
    return <InfoCard title={t('providers.ipRdap.notFound')} />;
  }

  const range = result.start_address && result.end_address
    ? `${result.start_address} – ${result.end_address}`
    : null;
  const abuseEmails = result.abuse_emails || [];

  return (
    <Card sx={{ p: 2, m: 1 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {[result.name, result.registry || result.registry_server].filter(Boolean).join(' · ')}
      </Typography>
      <FieldTable
        label={t('providers.ipRdap.title')}
        rows={[
          { name: t('providers.ipRdap.registrant'), value: result.registrant },
          { name: t('providers.ipRdap.handle'), value: result.handle },
          { name: t('providers.ipRdap.cidrs'), value: (result.cidrs || []).join(', ') },
          { name: t('providers.ipRdap.range'), value: range },
          { name: t('providers.ipRdap.type'), value: result.type },
          { name: t('providers.ipRdap.country'), value: result.country },
          { name: t('providers.ipRdap.registration'), value: formatDate(result.registration) },
          { name: t('providers.ipRdap.lastChanged'), value: formatDate(result.last_changed) },
          { name: t('providers.ipRdap.registryServer'), value: result.registry_server },
        ]}
      />
      {abuseEmails.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('providers.ipRdap.abuse')}</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
            {abuseEmails.map((email) => (
              <Chip
                key={email}
                label={email}
                size="small"
                variant="outlined"
                clickable
                onClick={() => navigate(buildPrefillUrl('/ioc-tools/lookup', email))}
              />
            ))}
          </Box>
        </Box>
      )}
    </Card>
  );
}
