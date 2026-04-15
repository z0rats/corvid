import React, { useState, useRef, useEffect } from 'react';
import IocLookupDialog from '../../../ioc-tools/ioc-lookup/shared/components/IocLookupDialog';
import { useIocLookupDialog } from '../../../ioc-tools/ioc-lookup/shared/hooks/useIocLookupDialog';
import { emailUtils } from '../../utils/emailUtils';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

const HASH_FIELDS = ['md5', 'sha1', 'sha256'];

function CopyButton({ value }) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    return () => clearTimeout(timeoutRef.current);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setCopied(false), 1500);
  };

  return (
    <Tooltip title={copied ? 'Copied!' : 'Copy'}>
      <IconButton size="small" onClick={handleCopy} sx={{ p: 0.25 }} aria-label="Copy hash">
        <ContentCopyIcon sx={{ fontSize: '0.875rem' }} />
      </IconButton>
    </Tooltip>
  );
}

function HashRow({ label, value }) {
  return (
    <Box sx={{ display: 'flex', py: 0.75, gap: 2 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 50, flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography
        variant="body2"
        sx={{ fontFamily: 'monospace', wordBreak: 'break-all', flex: 1 }}
      >
        {value}
      </Typography>
      <CopyButton value={value} />
    </Box>
  );
}

export default function EmlHashValues({ hashes }) {
  const { open, ioc, iocType, openDialog, closeDialog } = useIocLookupDialog();

  return (
    <>
      {HASH_FIELDS.map((hashType) => (
        <HashRow
          key={hashType}
          label={hashType.toUpperCase()}
          value={hashes[hashType]}
        />
      ))}
      <Box sx={{ mt: 1 }}>
        <Button
          variant="outlined"
          disableElevation
          size="small"
          sx={{ py: 0.25, px: 1.5, fontSize: '0.8125rem' }}
          onClick={() => openDialog(hashes.md5, emailUtils.getHashType(hashes.md5))}
        >
          Analyze .eml hash
        </Button>
      </Box>
      <IocLookupDialog open={open} onClose={closeDialog} ioc={ioc} iocType={iocType} />
    </>
  );
}
