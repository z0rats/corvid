import { useEffect, useMemo, useState } from 'react';
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
import { getMainMenuItems } from '../../config/sidebarConfig';
import { getRunPath } from '../../utils/historyPaths';
import { useVisibleModuleIds } from '../../hooks/useVisibleModuleIds';
import ScanStatusChip from '../ScanStatusChip';
import { createLogger } from '../../utils/logger';

const logger = createLogger('RecentActivity');

// Activity `feature` values that aren't a sidebar moduleId themselves.
const FEATURE_MODULE = {
  social_analyzer: 'username_search',
  threat_actor_usernames: 'username_search',
  ioc_lookup: 'ioc_tools',
};

/**
 * Start screen's "pick up where you left off": the newest runs across every feature with a saved
 * history, each linking straight to its result. Renders nothing until there is something to show.
 */
export default function RecentActivity({ limit = 8 }) {
  const { t } = useTranslation('commandPalette');
  const { t: tCommon } = useTranslation();
  const visibleModuleIds = useVisibleModuleIds();
  const [items, setItems] = useState([]);

  useEffect(() => {
    let ignore = false;
    activityService.listRecent(limit)
      .then((data) => { if (!ignore) setItems(data); })
      .catch((err) => logger.warn('Failed to load recent activity:', err));
    return () => { ignore = true; };
  }, [limit]);

  const modules = useMemo(
    () => Object.fromEntries(getMainMenuItems(tCommon).map((item) => [item.moduleId, item])),
    [tCommon],
  );

  const rows = items
    .map((item) => ({ item, module: modules[FEATURE_MODULE[item.feature] ?? item.feature] }))
    .filter(({ item, module }) => module && visibleModuleIds.has(module.moduleId) && getRunPath(item.feature, item.id));

  if (rows.length === 0) return null;

  return (
    <Box sx={{ mt: 4, width: '100%', maxWidth: 640, mx: 'auto' }}>
      <Typography variant="overline" color="text.secondary">{t('startScreen.recentActivity')}</Typography>
      <List dense disablePadding>
        {rows.map(({ item, module }) => (
          <ListItemButton
            key={`${item.feature}-${item.id}`}
            component={Link}
            to={getRunPath(item.feature, item.id)}
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
