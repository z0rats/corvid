import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { buildPrefillUrl } from '../../../../../../../core/utils/crossFeatureNav';
import NoDetails from '../NoDetails';
import { ReservedAddressCard } from '../StatusCard';

function ChipSection({ title, items, chipProps, onClick }) {
  if (!items?.length) return null;
  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>{title}</Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
        {items.map((item) => (
          <Chip
            key={item}
            label={item}
            size="small"
            variant="outlined"
            {...chipProps}
            {...(onClick ? { clickable: true, onClick: () => onClick(item) } : {})}
          />
        ))}
      </Box>
    </Box>
  );
}

export default function InternetDbDetails({ result }) {
  const { t } = useTranslation('iocTools');
  const navigate = useNavigate();

  if (!result) {
    return <NoDetails message={t('providers.internetdb.unavailable')} />;
  }

  if (result.reserved) {
    return <ReservedAddressCard />;
  }

  if (result.no_data) {
    return (
      <Card sx={{ p: 2, m: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <InfoOutlinedIcon color="action" />
          <Typography variant="h6">{t('providers.internetdb.noData')}</Typography>
        </Box>
      </Card>
    );
  }

  const { ports = [], hostnames = [], tags = [], cpes = [], vulns = [] } = result;

  return (
    <Card sx={{ p: 2, m: 1 }}>
      <Typography variant="h6">
        {t('providers.internetdb.headline', { ports: ports.length, vulns: vulns.length })}
      </Typography>
      <ChipSection
        title={t('providers.internetdb.vulns')}
        items={vulns}
        chipProps={{ color: 'error' }}
        onClick={(cve) => navigate(buildPrefillUrl('/ioc-tools/lookup', cve))}
      />
      <ChipSection title={t('providers.internetdb.ports')} items={ports.map(String)} />
      <ChipSection title={t('providers.internetdb.hostnames')} items={hostnames} />
      <ChipSection title={t('providers.internetdb.tags')} items={tags} />
      <ChipSection title={t('providers.internetdb.cpes')} items={cpes} />
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        {t('providers.internetdb.disclaimer')}
      </Typography>
    </Card>
  );
}
