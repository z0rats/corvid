import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import cytoscape from 'cytoscape';
import { useTheme } from '@mui/material/styles';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import DownloadIcon from '@mui/icons-material/DownloadOutlined';
import ScatterPlotIcon from '@mui/icons-material/ScatterPlotOutlined';

import { investigationsService } from '../../../core/services/api/investigationsService';
import { downloadFile, exportFileName } from '../../../core/utils/exportData';
import { createLogger } from '../../../core/utils/logger';
import { entityColor } from '../constants/entityTypes';
import { neighborsOf, toElements, typeCounts } from '../utils/graphElements';
import NodePanel from './NodePanel';

const logger = createLogger('EntityGraph');

const LAYOUT = { name: 'cose', animate: false, randomize: true, padding: 30, nodeDimensionsIncludeLabels: true };

function graphStyle(theme) {
  const text = theme.palette.text.primary;
  const muted = theme.palette.text.secondary;
  const line = theme.palette.divider;
  return [
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        width: 'data(size)',
        height: 'data(size)',
        label: 'data(label)',
        color: text,
        'font-size': 10,
        'text-valign': 'bottom',
        'text-margin-y': 4,
        'text-wrap': 'ellipsis',
        'text-max-width': '140px',
        'min-zoomed-font-size': 6,
      },
    },
    { selector: 'node[root = 1]', style: { 'border-width': 3, 'border-color': text } },
    { selector: 'node:selected', style: { 'border-width': 4, 'border-color': theme.palette.primary.main } },
    {
      selector: 'edge',
      style: {
        width: 1.2,
        'line-color': line,
        'curve-style': 'bezier',
        'target-arrow-shape': 'triangle',
        'target-arrow-color': line,
        'arrow-scale': 0.8,
        label: 'data(label)',
        color: muted,
        'font-size': 8,
        'text-rotation': 'autorotate',
        'text-background-color': theme.palette.background.paper,
        'text-background-opacity': 1,
        'text-background-padding': '1px',
        'min-zoomed-font-size': 8,
      },
    },
  ];
}

/**
 * The investigation's entity graph (backend derives it from the runs on every request, ADR 0028).
 * Type chips filter server-side, so the node cap applies to what is left after filtering.
 */
export default function EntityGraph({ investigationId, investigationName, featureLabels, refreshKey }) {
  const { t } = useTranslation('investigations');
  const theme = useTheme();
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [graph, setGraph] = useState(null);
  const [selectedTypes, setSelectedTypes] = useState(null); // null = every type
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    investigationsService
      .graph(investigationId, selectedTypes ? [...selectedTypes].sort() : null)
      .then((data) => {
        if (ignore) return;
        setGraph(data);
        setError(null);
      })
      .catch((err) => {
        logger.error('Failed to load graph:', err);
        if (!ignore) setError(t('graph.loadFailed'));
      })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [investigationId, selectedTypes, refreshKey, t]);

  const elements = useMemo(() => (graph ? toElements(graph) : []), [graph]);
  // Counted server-side before the type filter and the node cap, so a type the cap dropped
  // entirely still gets its chip, and counts stay current as items change.
  const allTypes = useMemo(() => (graph ? typeCounts(graph.type_counts) : []), [graph]);

  useEffect(() => {
    if (!containerRef.current || elements.length === 0) return undefined;
    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: graphStyle(theme),
      layout: LAYOUT,
      wheelSensitivity: 0.3,
    });
    cy.on('tap', 'node', (event) => setSelectedId(event.target.id()));
    cy.on('tap', (event) => { if (event.target === cy) setSelectedId(null); });
    cyRef.current = cy;
    return () => {
      cyRef.current = null;
      cy.destroy();
    };
  }, [elements, theme]);

  const toggleType = (type) => {
    const current = selectedTypes ?? new Set(allTypes.map(([name]) => name));
    const next = new Set(current);
    if (next.has(type)) {
      if (next.size === 1) return;
      next.delete(type);
    } else {
      next.add(type);
    }
    setSelectedId(null);
    setSelectedTypes(next.size === allTypes.length ? null : next);
  };

  const exportPng = () => {
    const blob = cyRef.current?.png({ output: 'blob', full: true, scale: 2, bg: theme.palette.background.paper });
    if (blob) downloadFile(blob, `${exportFileName('investigation', investigationName)}.png`, 'image/png');
  };

  const selectedNode = graph?.nodes.find((node) => node.id === selectedId) ?? null;
  const neighbors = selectedNode && graph ? neighborsOf(graph, selectedNode.id) : [];
  const isOn = (type) => !selectedTypes || selectedTypes.has(type);

  return (
    <Box>
      {allTypes.length > 0 && (
        <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">{t('graph.filterLabel')}:</Typography>
          {allTypes.map(([type, count]) => (
            <Chip
              key={type}
              size="small"
              clickable
              aria-pressed={isOn(type)}
              label={`${t(`graph.types.${type}`, { defaultValue: type })} (${count})`}
              onClick={() => toggleType(type)}
              variant={isOn(type) ? 'filled' : 'outlined'}
              sx={isOn(type) ? { bgcolor: entityColor(type), color: '#fff' } : undefined}
            />
          ))}
          {selectedTypes && (
            <Button size="small" onClick={() => setSelectedTypes(null)}>{t('graph.allTypes')}</Button>
          )}
          <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
            <Button size="small" startIcon={<CenterFocusStrongIcon />} onClick={() => cyRef.current?.fit(undefined, 30)}>
              {t('graph.fit')}
            </Button>
            <Button size="small" startIcon={<ScatterPlotIcon />} onClick={() => cyRef.current?.layout(LAYOUT).run()}>
              {t('graph.relayout')}
            </Button>
            <Button size="small" startIcon={<DownloadIcon />} onClick={exportPng} disabled={elements.length === 0}>
              {t('graph.exportPng')}
            </Button>
          </Box>
        </Stack>
      )}

      {loading && <LinearProgress sx={{ mb: 1 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {graph?.truncated && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t('graph.truncated', { shown: graph.nodes.length, total: graph.total_nodes })}
        </Alert>
      )}
      {graph && graph.nodes.length === 0 && !loading && (
        <Typography color="text.secondary">{t('graph.empty')}</Typography>
      )}

      {elements.length > 0 && (
        <>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Paper
              variant="outlined"
              ref={containerRef}
              data-testid="entity-graph-canvas"
              sx={{ flexGrow: 1, height: { xs: 420, md: 600 }, minWidth: 0 }}
            />
            {selectedNode && (
              <NodePanel
                node={selectedNode}
                neighbors={neighbors}
                featureLabels={featureLabels}
                onClose={() => setSelectedId(null)}
              />
            )}
          </Stack>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            {t('graph.legendRoot')}
          </Typography>
        </>
      )}
    </Box>
  );
}
