import React, { useState, useMemo, memo } from 'react';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { useTheme } from '@mui/material/styles';
import ServiceHeaderCell from '../../../shared/components/ServiceHeaderCell';
import { getServiceIcon } from '../../../shared/utils/iconUtils';
import { getTlpBackgroundColor } from '../../../shared/utils/tlpUtils';
import { SERVICE_DEFINITIONS } from '../../../shared/config/serviceConfig';

function ServiceRow({
  serviceName,
  serviceData,
  iocValue,
  iocType,
  avatarStyle: propAvatarStyle,
  cellStyle: propCellStyle
}) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);

  const config = SERVICE_DEFINITIONS[serviceName];
  const DetailComponent = config ? config.detailComponent : null;

  const rowBgColor = theme.palette.mode === 'dark' ? theme.palette.background.paper : 'inherit';
  const baseCellSx = useMemo(
    () => propCellStyle || { px: 2, py: 1.5, verticalAlign: "middle" },
    [propCellStyle]
  );
  const avatarStyle = useMemo(
    () => propAvatarStyle || { width: 30, height: 30, border: "1px solid", borderColor: theme.palette.divider },
    [propAvatarStyle, theme.palette.divider]
  );

  const iconSrc = getServiceIcon(config?.icon);
  const displayName = config?.name || serviceName;

  const tlpCellBgColor = getTlpBackgroundColor(serviceData.tlp, serviceData.status, theme);

  if (serviceData.status === 'loading') {
    return (
      <TableRow sx={{ backgroundColor: `${rowBgColor} !important` }}>
        <TableCell sx={{ ...baseCellSx, width: '40px' }}>
          <IconButton aria-label="expand row" size="small" disabled>
            <KeyboardArrowDownIcon />
          </IconButton>
        </TableCell>
        <TableCell sx={baseCellSx}>
          <ServiceHeaderCell iconSrc={iconSrc} serviceName={displayName} avatarStyle={avatarStyle} />
        </TableCell>
        <TableCell sx={baseCellSx}>
          <CircularProgress size={20} />
        </TableCell>
        <TableCell sx={{ ...baseCellSx, width: '40px', backgroundColor: 'transparent', p: 0 }} />
      </TableRow>
    );
  }

  if (serviceData.status === 'error') {
     return (
      <TableRow sx={{ backgroundColor: `${rowBgColor} !important` }}>
        <TableCell sx={{ ...baseCellSx, width: '40px' }}>
          <IconButton aria-label="expand row" size="small" disabled>
            <KeyboardArrowDownIcon />
          </IconButton>
        </TableCell>
        <TableCell sx={baseCellSx}>
          <ServiceHeaderCell iconSrc={iconSrc} serviceName={displayName} avatarStyle={avatarStyle} />
        </TableCell>
        <TableCell sx={baseCellSx}>
          <Typography variant="body2" noWrap title={serviceData.summary}>
            {serviceData.summary}
          </Typography>
        </TableCell>
        <TableCell sx={{ ...baseCellSx, width: '40px', backgroundColor: tlpCellBgColor, p: 0 }} />
      </TableRow>
    );
  }

  return (
    <>
      <TableRow sx={{ backgroundColor: `${rowBgColor} !important` }}>
        <TableCell sx={{ ...baseCellSx, width: '40px' }}>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
            disabled={!serviceData.data || !DetailComponent}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell sx={baseCellSx}>
          <ServiceHeaderCell iconSrc={iconSrc} serviceName={displayName} avatarStyle={avatarStyle} />
        </TableCell>
        <TableCell sx={baseCellSx}>
          <Typography variant="body2" noWrap title={serviceData.summary}>
            {serviceData.summary || 'No summary'}
          </Typography>
        </TableCell>
        <TableCell
          sx={{
            verticalAlign: 'middle',
            width: '40px',
            backgroundColor: tlpCellBgColor,
            p: 0,
            borderLeft: 1,
            borderLeftColor: 'divider',
          }}
          title={`TLP: ${serviceData.tlp || 'N/A'}`}
        >
          &nbsp;
        </TableCell>
      </TableRow>

      {DetailComponent && serviceData.data && (
        <TableRow sx={{ backgroundColor: `${rowBgColor} !important` }}>
          <TableCell
            sx={{
              pb: open ? 2 : 0,
              pt: 0,
              pl: '56px',
              pr: 2,
              borderBottom: open ? 1 : 'none',
              borderBottomColor: 'divider',
              bgcolor: 'background.detailArea',
            }}
            colSpan={4}
          >
            <Collapse in={open} timeout="auto" unmountOnExit>
              <Box sx={{ margin: 1, mt:2, mb:2 }}>
                <DetailComponent
                  result={serviceData.data}
                  ioc={iocValue}
                  type={iocType}
                />
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

export default memo(ServiceRow);
