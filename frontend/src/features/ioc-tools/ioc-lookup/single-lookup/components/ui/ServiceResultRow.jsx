import React, { useState, useMemo, memo } from "react";
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
          <Typography color="error">Error: Service details missing for row.</Typography>
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
      let detailMessage = "No further details available for this error.";
      
      if (result.error === 429 && result.is_rate_limited) {
        detailMessage = (
          <Box>
            <Typography variant="body2" color="error" gutterBottom>
              <strong>Quota consumed. No API calls left.</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {result.message}
            </Typography>
            {result.retry_after && result.retry_after !== 'unknown' && (
              <Typography variant="body2" color="text.secondary">
                Retry after: {result.retry_after} seconds
              </Typography>
            )}
            {result.rate_limit_reset && result.rate_limit_reset !== 'unknown' && (
              <Typography variant="body2" color="text.secondary">
                Limit resets at: {result.rate_limit_reset}
              </Typography>
            )}
            {result.rate_limit_remaining && result.rate_limit_remaining !== 'unknown' && (
              <Typography variant="body2" color="text.secondary">
                Remaining requests: {result.rate_limit_remaining}
              </Typography>
            )}
          </Box>
        );
      } else if (result.message && result.error !== 404) {
        detailMessage = result.message;
      } else if (result.error === 404) {
        detailMessage = "The requested item was not found by the service.";
      } else if (result.error) {
        detailMessage = `An error (${result.error}) occurred.`;
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
        return <Box sx={{ p: 2, textAlign: 'center' }}><Typography variant="body2" color="text.secondary">No specific details component for this result.</Typography></Box>;
    }

    return (
      <Box sx={{ p: 2, overflowX: 'auto' }}>
        <Typography variant="caption" display="block" gutterBottom color="text.secondary">Raw JSON Data:</Typography>
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
          <IconButton aria-label="expand row" size="small" disabled><KeyboardArrowDownIcon /></IconButton>
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
            aria-label="expand row" size="small" onClick={() => setOpen(!open)}
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
          title={`TLP: ${tlp}`}
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
