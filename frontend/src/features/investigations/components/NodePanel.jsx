import { useTranslation } from 'react-i18next';
import { Link as RouterLink, useNavigate } from 'react-router';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';
import { getRunPath } from '../../../core/utils/historyPaths';
import { entityColor, entityPivots } from '../constants/entityTypes';
import { externalUrl } from '../utils/graphElements';

const pivotValue = (node) => node.raw_value ?? node.value;

/** Where a node can be looked up next: its own type's features, with the value as the source
 * gave it. An account has no feature of its own, so it offers its linked username's instead. */
function pivotTargets(node, neighbors) {
  const own = entityPivots(node.type).map((pivot) => ({ pivot, value: pivotValue(node) }));
  if (node.type !== 'account') return own;
  return neighbors
    .filter((neighbor) => neighbor.type === 'username')
    .flatMap((username) => entityPivots('username').map((pivot) => ({ pivot, value: pivotValue(username) })));
}

/** Side panel for the selected graph node: what it is, which runs produced it, and where it can
 * be looked up next. */
export default function NodePanel({ node, neighbors = [], featureLabels, onClose }) {
  const { t } = useTranslation('investigations');
  const navigate = useNavigate();
  const url = externalUrl(node);
  const pivots = pivotTargets(node, neighbors);
  const showValues = new Set(pivots.map((target) => target.value)).size > 1 || node.type === 'account';

  return (
    <Paper variant="outlined" sx={{ p: 2, width: { xs: '100%', md: 300 }, flexShrink: 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Chip
          size="small"
          label={t(`graph.types.${node.type}`, { defaultValue: node.type })}
          sx={{ bgcolor: entityColor(node.type), color: '#fff' }}
        />
        <Typography variant="body2" color="text.secondary">
          {t('graph.panel.links', { count: node.degree })}
        </Typography>
        <IconButton size="small" onClick={onClose} aria-label={t('graph.panel.close')} sx={{ ml: 'auto' }}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>
      <Typography sx={{ fontFamily: '"JetBrains Mono", monospace', wordBreak: 'break-all', mb: 2 }}>
        {node.label}
      </Typography>

      {url && (
        <Button
          size="small"
          variant="outlined"
          endIcon={<OpenInNewIcon />}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          sx={{ mb: 2 }}
        >
          {t('graph.panel.open')}
        </Button>
      )}

      {pivots.length > 0 && (
        <>
          <Typography variant="overline" color="text.secondary">{t('graph.panel.pivot')}</Typography>
          <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', rowGap: 1 }}>
            {pivots.map(({ pivot, value }) => (
              <Button
                key={`${pivot.key}-${value}`}
                size="small"
                variant="outlined"
                onClick={() => navigate(buildPrefillUrl(pivot.path, value))}
              >
                {t(`graph.panel.pivots.${pivot.key}`)}{showValues ? `: ${value}` : ''}
              </Button>
            ))}
          </Stack>
        </>
      )}

      <Typography variant="overline" color="text.secondary">{t('graph.panel.foundBy')}</Typography>
      <Stack spacing={0.5}>
        {node.sources.map((source) => (
          <Link
            key={`${source.feature}-${source.run_id}`}
            component={RouterLink}
            to={getRunPath(source.feature, source.run_id) ?? '#'}
            variant="body2"
          >
            {featureLabels[source.feature] ?? source.feature} #{source.run_id}
          </Link>
        ))}
      </Stack>
    </Paper>
  );
}
