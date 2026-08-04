import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useImageStructure } from '../../hooks/api/useImageStructure';
import PixelAnalysisPanel from './PixelAnalysisPanel';

function FrameSummary({ frame, overallQualityEstimate, compressionRatio, bitsPerPixel }) {
  const { t } = useTranslation('imageTools');
  if (!frame) return null;

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
      <Chip size="small" label={`${frame.width} × ${frame.height} px`} />
      <Chip size="small" label={frame.is_progressive ? t('structureAnalyzer.progressive') : t('structureAnalyzer.baseline')} />
      <Chip size="small" label={frame.chroma_subsampling} />
      {overallQualityEstimate != null && (
        <Chip size="small" color="primary" label={t('structureAnalyzer.qualityEstimate', { value: overallQualityEstimate })} />
      )}
      {compressionRatio != null && (
        <Chip size="small" variant="outlined" label={t('structureAnalyzer.compressionRatio', { value: compressionRatio })} />
      )}
      {bitsPerPixel != null && (
        <Chip size="small" variant="outlined" label={t('structureAnalyzer.bitsPerPixel', { value: bitsPerPixel })} />
      )}
    </Box>
  );
}

function QuantizationTables({ tables }) {
  const { t } = useTranslation('imageTools');
  if (!tables?.length) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('structureAnalyzer.quantizationTables')}</Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        {tables.map((table) => (
          <Box key={table.table_id} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {t('structureAnalyzer.tableId', { id: table.table_id })}
              {table.quality_estimate != null ? ` · ${t('structureAnalyzer.qualityEstimate', { value: table.quality_estimate })}` : ''}
            </Typography>
            <Table size="small" sx={{ mt: 0.5 }}>
              <TableBody>
                {Array.from({ length: 8 }).map((_, row) => (
                  <TableRow key={row}>
                    {Array.from({ length: 8 }).map((__, col) => (
                      <TableCell key={col} sx={{ p: '2px 6px', fontFamily: 'monospace', fontSize: '0.7rem', border: 'none' }}>
                        {table.values[row * 8 + col]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

function HuffmanTables({ tables }) {
  const { t } = useTranslation('imageTools');
  if (!tables?.length) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('structureAnalyzer.huffmanTables')}</Typography>
      {tables.map((table) => (
        <Box key={`${table.table_class}-${table.table_id}`} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <Chip size="small" label={`${table.table_class} #${table.table_id}`} />
          <Typography variant="body2" color="text.secondary">
            {t('structureAnalyzer.totalCodes', { count: table.total_codes })}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}

function MarkerRow({ marker }) {
  const { t } = useTranslation('imageTools');
  const [showHex, setShowHex] = useState(false);
  const hasHex = Boolean(marker.raw_hex);

  return (
    <Box sx={{ borderBottom: '1px solid', borderColor: 'divider', py: 0.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Typography variant="body2" sx={{ minWidth: 90, fontWeight: 500 }}>{marker.marker_type}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ minWidth: 60, fontFamily: 'monospace' }}>{marker.marker_code}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ minWidth: 90 }}>
          {t('structureAnalyzer.offset', { value: marker.offset })}
        </Typography>
        {marker.length != null && (
          <Typography variant="body2" color="text.secondary">
            {t('structureAnalyzer.length', { value: marker.length })}
          </Typography>
        )}
        {hasHex && (
          <IconButton size="small" onClick={() => setShowHex(!showHex)} sx={{ ml: 'auto' }}>
            <ExpandMoreIcon sx={{ transform: showHex ? 'rotate(180deg)' : 'none', fontSize: '1.1rem' }} />
          </IconButton>
        )}
      </Box>
      {showHex && hasHex && (
        <Typography variant="caption" sx={{ display: 'block', fontFamily: 'monospace', wordBreak: 'break-all', color: 'text.secondary', mt: 0.5 }}>
          {marker.raw_hex}{marker.truncated ? '…' : ''}
        </Typography>
      )}
    </Box>
  );
}

export default function ImageStructurePanel({ file, format }) {
  const { t } = useTranslation('imageTools');
  const { result, loading, error, analyzeStructure } = useImageStructure();
  const isJpeg = (format || '').toUpperCase() === 'JPEG';

  useEffect(() => {
    if (isJpeg && file) {
      analyzeStructure(file);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file, isJpeg]);

  if (!isJpeg) {
    return (
      <Alert severity="info">{t('structureAnalyzer.jpegOnly')}</Alert>
    );
  }

  return (
    <Box>
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <FrameSummary
            frame={result.frame}
            overallQualityEstimate={result.overall_quality_estimate}
            compressionRatio={result.compression_ratio}
            bitsPerPixel={result.bits_per_pixel}
          />
          <QuantizationTables tables={result.quantization_tables} />
          <HuffmanTables tables={result.huffman_tables} />

          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            {t('structureAnalyzer.markerMap', { count: result.markers.length })}
          </Typography>
          <Box>
            {result.markers.map((marker, index) => (
              <MarkerRow key={`${marker.offset}-${index}`} marker={marker} />
            ))}
          </Box>

          <PixelAnalysisPanel file={file} />
        </Box>
      )}
    </Box>
  );
}
