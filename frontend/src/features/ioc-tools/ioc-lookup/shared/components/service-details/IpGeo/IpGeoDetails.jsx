import React from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import NoDetails from '../NoDetails';
import FieldTable from '../FieldTable';
import { ReservedAddressCard } from '../StatusCard';

export default function IpGeoDetails({ result }) {
  const { t } = useTranslation('iocTools');

  if (!result) {
    return <NoDetails message={t('providers.ipGeo.unavailable')} />;
  }
  if (result.reserved) {
    return <ReservedAddressCard />;
  }

  const place = [result.city, result.region, result.country].filter(Boolean).join(', ');
  const coordinates = result.lat != null && result.lon != null ? `${result.lat}, ${result.lon}` : null;

  return (
    <Card sx={{ p: 2, m: 1 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>{place || t('providers.ipGeo.unknownLocation')}</Typography>
      <FieldTable
        label={t('providers.ipGeo.title')}
        rows={[
          { name: t('providers.ipGeo.asn'), value: result.asn },
          { name: t('providers.ipGeo.company'), value: result.company },
          { name: t('providers.ipGeo.country'), value: result.country },
          { name: t('providers.ipGeo.region'), value: result.region },
          { name: t('providers.ipGeo.city'), value: result.city },
          { name: t('providers.ipGeo.coordinates'), value: coordinates },
          { name: t('providers.ipGeo.timezone'), value: result.timezone },
        ]}
      />
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        {t('providers.ipGeo.disclaimer')}
      </Typography>
    </Card>
  );
}
