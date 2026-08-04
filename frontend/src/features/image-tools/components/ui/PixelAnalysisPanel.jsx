import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import { useImageVisualAnalysis } from '../../hooks/api/useImageVisualAnalysis';

function HistogramChart({ label, color, counts }) {
  const max = Math.max(...counts, 1);
  const points = counts
    .map((count, i) => {
      const x = (i / 255) * 100;
      const y = 100 - (Math.log1p(count) / Math.log1p(max)) * 100;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <Box sx={{ flex: '1 1 140px', minWidth: 140 }}>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Box
        component="svg"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        sx={{ width: '100%', height: 60, display: 'block', bgcolor: 'action.hover', borderRadius: 0.5 }}
      >
        <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      </Box>
    </Box>
  );
}

function VectorscopeCanvas({ vectorscope }) {
  const { t } = useTranslation('imageTools');
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!vectorscope || !canvasRef.current) return;
    const { bin_count: binCount, counts, max_count: maxCount } = vectorscope;
    const canvas = canvasRef.current;
    canvas.width = binCount;
    canvas.height = binCount;
    const ctx = canvas.getContext('2d');
    if (!ctx) return; // e.g. no canvas support in the current environment

    const imageData = ctx.createImageData(binCount, binCount);

    for (let i = 0; i < counts.length; i++) {
      // sqrt spreads low counts out more visibly than a linear scale would
      const intensity = maxCount > 0 ? Math.sqrt(counts[i] / maxCount) : 0;
      const value = Math.round(intensity * 255);
      imageData.data[i * 4] = value;
      imageData.data[i * 4 + 1] = value;
      imageData.data[i * 4 + 2] = value;
      imageData.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(imageData, 0, 0);
  }, [vectorscope]);

  return (
    <Box>
      <Typography variant="caption" color="text.secondary">{t('pixelAnalysis.vectorscope')}</Typography>
      <Box
        component="canvas"
        ref={canvasRef}
        sx={{
          width: 200, height: 200, display: 'block', mt: 0.5,
          bgcolor: '#000', borderRadius: 0.5, imageRendering: 'pixelated',
        }}
      />
    </Box>
  );
}

export default function PixelAnalysisPanel({ file }) {
  const { t } = useTranslation('imageTools');
  const { result, loading, error, analyzeVisuals } = useImageVisualAnalysis();

  useEffect(() => {
    if (file) {
      analyzeVisuals(file);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  return (
    <Box sx={{ mt: 3 }}>
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('pixelAnalysis.title')}</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
            <HistogramChart label={t('pixelAnalysis.red')} color="#e53935" counts={result.histograms.red} />
            <HistogramChart label={t('pixelAnalysis.green')} color="#43a047" counts={result.histograms.green} />
            <HistogramChart label={t('pixelAnalysis.blue')} color="#1e88e5" counts={result.histograms.blue} />
            <HistogramChart label={t('pixelAnalysis.luminance')} color="#9e9e9e" counts={result.histograms.luminance} />
            <HistogramChart label={t('pixelAnalysis.cb')} color="#26c6da" counts={result.histograms.cb} />
            <HistogramChart label={t('pixelAnalysis.cr')} color="#ff7043" counts={result.histograms.cr} />
          </Box>
          <VectorscopeCanvas vectorscope={result.vectorscope} />
        </Box>
      )}
    </Box>
  );
}
