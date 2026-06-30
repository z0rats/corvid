import React from 'react';
import { useTranslation } from 'react-i18next';
import Avatar from '@mui/material/Avatar';
import CardHeader from '@mui/material/CardHeader';

function ServiceHeaderCell({ iconSrc, serviceName, avatarStyle, headerProps }) {
  const { t } = useTranslation('iocTools');

  const avatar = iconSrc ? (
    <Avatar
      alt={t('iocLookupShared.serviceHeaderCell.iconAlt', { serviceName })}
      src={iconSrc}
      sx={avatarStyle}
      variant="rounded"
    />
  ) : (
    <Avatar sx={avatarStyle} variant="rounded">
      {serviceName.charAt(0).toUpperCase()}
    </Avatar>
  );

  return (
    <CardHeader
      avatar={avatar}
      title={serviceName}
      sx={{ padding: 0 }}
      titleTypographyProps={{ variant: 'body2', fontWeight: 'medium' }}
      {...headerProps}
    />
  );
}

export default ServiceHeaderCell;
