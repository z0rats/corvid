import React, { useState, useRef, useEffect } from 'react';
import IocLookupDialog from '../../../ioc-tools/ioc-lookup/shared/components/IocLookupDialog';
import { useIocLookupDialog } from '../../../ioc-tools/ioc-lookup/shared/hooks/useIocLookupDialog';
import { emailUtils } from '../../utils/emailUtils';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const HASH_FIELDS = ['md5', 'sha1', 'sha256'];

function CopyButton({ value }) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    return () => clearTimeout(timeoutRef.current);
  }, []);

  const handleCopy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(value);
    setCopied(true);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setCopied(false), 1500);
  };

  return (
    <Tooltip title={copied ? 'Copied!' : 'Copy'}>
      <IconButton size="small" onClick={handleCopy} sx={{ ml: 0.5 }} aria-label="Copy hash">
        <ContentCopyIcon sx={{ fontSize: '0.75rem' }} />
      </IconButton>
    </Tooltip>
  );
}

function AttachmentTable({ attachment, theme, onAnalyze }) {
  return (
    <TableContainer sx={{ maxWidth: '100%', mb: 2, boxShadow: 0, borderRadius: 1 }}>
      <Table size="small" aria-label="attachments table">
        <TableHead>
          <TableRow>
            <TableCell
              colSpan={3}
              sx={{ backgroundColor: theme.palette.background.tablecell, py: 1 }}
            >
              <Typography variant="subtitle2" component="div" fontWeight="bold">
                {attachment.filename ?? 'Unknown filename'}
              </Typography>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {HASH_FIELDS.map((hashType) => (
            <TableRow key={hashType}>
              <TableCell align="left" sx={{ width: '80px', py: 0.75 }}>
                <Typography variant="body2" fontWeight="medium">{hashType.toUpperCase()}</Typography>
              </TableCell>
              <TableCell align="left" sx={{ overflowWrap: 'anywhere', py: 0.75 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body2" fontFamily="monospace" fontSize="0.8125rem" sx={{ flex: 1 }}>
                    {attachment[hashType]}
                  </Typography>
                  <CopyButton value={attachment[hashType]} />
                </Box>
              </TableCell>
              <TableCell align="right" sx={{ width: '100px', py: 0.75 }}>
                <Button
                  variant="outlined"
                  disableElevation
                  size="small"
                  onClick={() => onAnalyze(attachment[hashType])}
                >
                  Analyze
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default function Attachments({ result }) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  const { open, ioc, iocType, openDialog, closeDialog } = useIocLookupDialog();

  const handleAnalyze = (hash) => {
    openDialog(hash, emailUtils.getHashType(hash));
  };

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="attachments-content"
        id="attachments-header"
        sx={{ minHeight: '48px', padding: '0 16px' }}
      >
        <Box display="flex" alignItems="center">
          <AttachFileIcon sx={{ mr: 1 }} fontSize="small" />
          <Typography variant="subtitle1" fontWeight="medium">
            Attachments ({result.length})
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 2 }}>
        {result.length > 0 ? (
          result.map((attachment) => (
            <AttachmentTable
              key={attachment.md5}
              attachment={attachment}
              theme={theme}
              onAnalyze={handleAnalyze}
            />
          ))
        ) : (
          <Typography variant="body2" sx={{ px: 1 }}>
            No attachments found
          </Typography>
        )}
        <IocLookupDialog open={open} onClose={closeDialog} ioc={ioc} iocType={iocType} />
      </AccordionDetails>
    </Accordion>
  );
}
