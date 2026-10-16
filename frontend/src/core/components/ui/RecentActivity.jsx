import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router';
import { formatDistanceToNow } from 'date-fns';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import { activityService } from '../../services/api/activityService';
import { useActivityRows } from '../../hooks/useActivityRows';
import ScanStatusChip from '../ScanStatusChip';
import { createLogger } from '../../utils/logger';

const logger = createLogger('RecentActivity');

// Re-fetched on this interval only while a listed run is still unfinished, so a running scan's
// row flips to its outcome without a page reload - and an idle feed costs no polling at all.
export const RECENT_ACTIVITY_LIVE_INTERVAL_MS = 5_000;
const UNFINISHED = new Set(['running', 'queued']);

/**
 * Start screen's "pick up where you left off": the newest runs across every feature with a saved
 * history, each linking straight to its result. Renders nothing until there is something to show.
 */
export default function RecentActivity({ limit = 8 }) {
  const { t } = useTranslation('commandPalette');
  const [items, setItems] = useState([]);
  const hasUnfinished = items.some((item) => UNFINISHED.has(item.status));

  useEffect(() => {
    let ignore = false;
    const load = () => activityService.listRecent(limit)
      .then((data) => { if (!ignore) setItems(data); })
      .catch((err) => logger.warn('Failed to load recent activity:', err));
    load();
    const id = hasUnfinished ? setInterval(load, RECENT_ACTIVITY_LIVE_INTERVAL_MS) : null;
    return () => {
      ignore = true;
      if (id) clearInterval(id);
    };
  }, [limit, hasUnfinished]);

  const rows = useActivityRows(items);

  if (rows.length === 0) return null;

  return (
    <Box sx={{ mt: 4, width: '100%', maxWidth: 640, mx: 'auto' }}>
      <Typography variant="overline" color="text.secondary">{t('startScreen.recentActivity')}</Typography>
      <List dense disablePadding>
        {rows.map(({ item, module, path }) => (
          <ListItemButton
            key={`${item.feature}-${item.id}`}
            component={Link}
            to={path}
            sx={{ borderRadius: 1 }}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>{module.icon}</ListItemIcon>
            <ListItemText
              primary={item.target}
              secondary={`${module.label} · ${formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}`}
              slotProps={{
                primary: { noWrap: true, sx: { fontFamily: '"JetBrains Mono", monospace', fontSize: '0.85rem' } },
              }}
            />
            {item.status !== 'completed' && (
              <ScanStatusChip status={item.status} label={t(`startScreen.activityStatus.${item.status}`)} />
            )}
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}
