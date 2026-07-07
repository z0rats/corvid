import React, { useState, useMemo, memo } from "react";
import { useTranslation } from 'react-i18next';
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import ServiceHeaderCell from '../../../shared/components/ServiceHeaderCell';
import { getServiceIcon } from '../../../shared/utils/iconUtils';
import { getTlpBackgroundColor } from '../../../shared/utils/tlpUtils';

function ServiceResultRow({
  serviceKey,
  service,
  loading,
  result,
  summary,
  tlp,
  ioc,
  iocType
}) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const [open, setOpen] = useState(false);

  const tlpCellBgColor = useMemo(
    () => getTlpBackgroundColor(tlp, loading ? 'loading' : (result?.error ? 'error' : 'success'), theme),
    [tlp, loading, result?.error, theme]
  );

  if (!service || !service.name) {
    return (
      <TableRow key={serviceKey || "service-config-error"}>
        <TableCell colSpan={4}>
          <Typography color="error">{t('singleLookup.serviceResultRow.errors.serviceDetailsMissing')}</Typography>
        </TableCell>
      </TableRow>
    );
  }

  const rowBgColor = theme.palette.mode === 'dark' ? theme.palette.background.paper : 'inherit';
  const baseCellSx = { p: 2, verticalAlign: "middle" };
  const avatarStyle = { width: 30, height: 30, border: "1px solid", borderColor: theme.palette.divider };

  const iconSrc = getServiceIcon(service.icon);

  const DetailComponentToRender = service.detailComponent; 

  const renderDetailsContent = () => {
    if (result?.error && !DetailComponentToRender) {
      let detailMessage = t('singleLookup.serviceResultRow.errors.noFurtherDetails');

      if (result.error === 429 && result.is_rate_limited) {
        detailMessage = (
          <Box>
            <Typography variant="body2" color="error" gutterBottom>
              <strong>{t('singleLookup.serviceResultRow.errors.quotaConsumed')}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {result.message}
            </Typography>
            {result.retry_after && result.retry_after !== 'unknown' && (
              <Typography variant="body2" color="text.secondary">
                {t('singleLookup.serviceResultRow.errors.retryAfter', { seconds: result.retry_after })}
              </Typography>
            )}
            {result.rate_limit_reset && result.rate_limit_reset !== 'unknown' && (
              <Typography variant="body2" color="text.secondary">
                {t('singleLookup.serviceResultRow.errors.limitResetsAt', { time: result.rate_limit_reset })}
              </Typography>
            )}
            {result.rate_limit_remaining && result.rate_limit_remaining !== 'unknown' && (
              <Typography variant="body2" color="text.secondary">
                {t('singleLookup.serviceResultRow.errors.remainingRequests', { count: result.rate_limit_remaining })}
              </Typography>
            )}
          </Box>
        );
      } else if (result.message && result.error !== 404) {
        detailMessage = result.message;
      } else if (result.error === 404) {
        detailMessage = t('singleLookup.serviceResultRow.errors.notFound');
      } else if (result.error) {
        detailMessage = t('singleLookup.serviceResultRow.errors.genericError', { code: result.error });
      }
      
      return (
        <Box sx={{ p: 2, textAlign: 'center' }}>
          {typeof detailMessage === 'string' ? (
            <Typography variant="body2" color="text.secondary">{detailMessage}</Typography>
          ) : (
            detailMessage
          )}
        </Box>
      );
    }
    
    if (DetailComponentToRender) {
      return <DetailComponentToRender result={result} ioc={ioc} type={iocType} />;
    }

    if (!result || result.error) {
        return <Box sx={{ p: 2, textAlign: 'center' }}><Typography variant="body2" color="text.secondary">{t('singleLookup.serviceResultRow.errors.noDetailsComponent')}</Typography></Box>;
    }

    return (
      <Box sx={{ p: 2, overflowX: 'auto' }}>
        <Typography variant="caption" sx={{ display: 'block' }} gutterBottom color="text.secondary">{t('singleLookup.serviceResultRow.rawJsonLabel')}</Typography>
        <Box
          component="pre"
          sx={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            fontSize: '12px',
            backgroundColor: 'background.paper',
            p: 1.25,
            borderRadius: 0.5,
            border: 1,
            borderColor: 'divider',
            maxHeight: '400px',
            overflowY: 'auto',
          }}
        >
          {JSON.stringify(result, null, 2)}
        </Box>
      </Box>
    );
  };

  if (loading) {
    return (
      <TableRow key={`${serviceKey}-loading`} sx={{ backgroundColor: `${rowBgColor} !important` }}>
        <TableCell sx={{ ...baseCellSx, width: '5%' }}>
          <IconButton aria-label={t('singleLookup.serviceResultRow.expandRowAriaLabel')} size="small" disabled><KeyboardArrowDownIcon /></IconButton>
        </TableCell>
        <TableCell sx={{ ...baseCellSx, width: '25%' }}>
          <ServiceHeaderCell iconSrc={iconSrc} serviceName={service.name} avatarStyle={avatarStyle} />
        </TableCell>
        <TableCell sx={{ ...baseCellSx, width: '65%' }}>
          <CircularProgress size={20} sx={{ marginRight: 1, verticalAlign: 'middle' }} />
          <Typography variant="body2" component="span" sx={{ verticalAlign: 'middle' }}>{summary}</Typography>
        </TableCell>
        <TableCell sx={{ ...baseCellSx, width: '5%', backgroundColor: tlpCellBgColor, p: 0 }}>&nbsp;</TableCell>
      </TableRow>
    );
  }

  const isExpandDisabled = !DetailComponentToRender && (!result || !!result.error);


  return (
    <>
      <TableRow key={`${serviceKey}-data`} sx={{ backgroundColor: `${rowBgColor} !important`, '& > *': { borderBottom: 'unset' } }}>
        <TableCell sx={{ ...baseCellSx, width: '5%' }}>
          <IconButton
            aria-label={t('singleLookup.serviceResultRow.expandRowAriaLabel')} size="small" onClick={() => setOpen(!open)}
            disabled={isExpandDisabled}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell sx={{ ...baseCellSx, width: '25%' }}>
          <ServiceHeaderCell iconSrc={iconSrc} serviceName={service.name} avatarStyle={avatarStyle} />
        </TableCell>
        <TableCell sx={{ ...baseCellSx, width: '65%' }}>
          <Typography variant="body2" noWrap title={summary}>{summary}</Typography>
        </TableCell>
        <TableCell
          sx={{ verticalAlign: 'middle', width: '5%', backgroundColor: tlpCellBgColor, p: 0, borderLeft: 1, borderLeftColor: 'divider' }}
          title={t('singleLookup.serviceResultRow.tlpTooltip', { tlp })}
        >
          &nbsp;
        </TableCell>
      </TableRow>
      <TableRow key={`${serviceKey}-details`} sx={{ backgroundColor: `${rowBgColor} !important` }}>
        <TableCell sx={{ pb: open ? 2 : 0, pt: 0, pl: '56px', pr: 2, borderBottom: open ? 1 : 'none', borderBottomColor: 'divider', bgcolor: 'background.detailArea' }} colSpan={4}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1, marginTop: 2, marginBottom: 2 }}>
                {renderDetailsContent()}
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default memo(ServiceResultRow);
