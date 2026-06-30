import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { imageUtils } from '../../utils/imageUtils';

const HASH_FIELDS = ['md5', 'sha1', 'sha256'];

function CopyButton({ value }) {
  const { t } = useTranslation('imageTools');
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
    <Tooltip title={copied ? t('fileMetadata.copied') : t('fileMetadata.copy')}>
      <IconButton size="small" onClick={handleCopy} sx={{ p: 0.25 }} aria-label={t('fileMetadata.copyHashAriaLabel')}>
        <ContentCopyIcon sx={{ fontSize: '0.875rem' }} />
      </IconButton>
    </Tooltip>
  );
}

function InfoRow({ label, value }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <Box sx={{ display: 'flex', py: 0.5, gap: 2 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 90, flexShrink: 0 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ wordBreak: 'break-all', flex: 1 }}>
        {value}
      </Typography>
    </Box>
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

export default function FileMetadata({ fileInfo, hashes }) {
  const { t } = useTranslation('imageTools');

  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      <Box sx={{ flex: 1, minWidth: 240 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          {t('fileMetadata.fileProperties')}
        </Typography>
        <InfoRow label={t('fileMetadata.format')} value={fileInfo?.format} />
        <InfoRow label={t('fileMetadata.mimeType')} value={fileInfo?.mime_type} />
        <InfoRow label={t('fileMetadata.dimensions')} value={fileInfo?.width && fileInfo?.height ? `${fileInfo.width} × ${fileInfo.height} px` : null} />
        <InfoRow label={t('fileMetadata.colorMode')} value={fileInfo?.mode} />
        <InfoRow label={t('fileMetadata.dpi')} value={fileInfo?.dpi_x ? `${fileInfo.dpi_x} × ${fileInfo.dpi_y}` : null} />
        <InfoRow label={t('fileMetadata.fileSize')} value={imageUtils.formatFileSize(fileInfo?.file_size)} />
      </Box>

      <Divider orientation="vertical" flexItem />

      <Box sx={{ flex: 1, minWidth: 240 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          {t('fileMetadata.fileHashes')}
        </Typography>
        {HASH_FIELDS.map((hashType) => (
          <HashRow key={hashType} label={hashType.toUpperCase()} value={hashes?.[hashType]} />
        ))}
      </Box>
    </Box>
  );
}
