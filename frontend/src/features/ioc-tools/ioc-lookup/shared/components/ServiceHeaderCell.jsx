import React from 'react';
import Avatar from '@mui/material/Avatar';
import CardHeader from '@mui/material/CardHeader';

function ServiceHeaderCell({ iconSrc, serviceName, avatarStyle, headerProps }) {
  const avatar = iconSrc ? (
    <Avatar
      alt={`${serviceName} icon`}
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
