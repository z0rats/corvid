import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListSubheader from '@mui/material/ListSubheader';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import PushPinIcon from '@mui/icons-material/PushPin';
import { buildCommandRegistry } from '../../config/commandRegistry';
import { getPinnedToolIds, getRecents, togglePinnedToolId, PINNED_CHANGED_EVENT } from '../../utils/commandPaletteStorage';

/**
 * Global tool catalog — replaces both TopNavMenu (top bar) and the mobile drawer's flat tool
 * list (see docs/command-palette-plan.md's Left panel section). Renders leftmost, with the
 * existing per-feature sub-tab Drawer (SidebarTabs) unchanged immediately to its right when a
 * feature has sub-tabs — confirmed as two stacked panels rather than one replacing the other.
 */
export default function LeftPanel({ sidebarOpen, filteredModuleIds }) {
  const { t } = useTranslation('commandPalette');
  // sidebarConfig.jsx's i18nKeys (nav.*) live in the default 'common' namespace.
  const { t: tCommon } = useTranslation();
  const location = useLocation();
  const [pinnedIds, setPinnedIds] = useState(getPinnedToolIds);
  const [recents, setRecents] = useState(getRecents);

  const registry = useMemo(() => buildCommandRegistry(tCommon), [tCommon]);

  useEffect(() => {
    // Storage is written synchronously by the palette (pin/recent) before it navigates, so
    // re-reading on every route change picks up palette-driven changes without a shared store.
    setPinnedIds(getPinnedToolIds());
    setRecents(getRecents());
  }, [location.pathname]);

  useEffect(() => {
    // Pinning/unpinning from the palette's action panel (or this panel's own unpin button below)
    // doesn't navigate anywhere, so the route-change effect above wouldn't otherwise catch it —
    // this is what makes a pin show up immediately instead of only after the next navigation.
    const handlePinnedChanged = () => setPinnedIds(getPinnedToolIds());
    window.addEventListener(PINNED_CHANGED_EVENT, handlePinnedChanged);
    return () => window.removeEventListener(PINNED_CHANGED_EVENT, handlePinnedChanged);
  }, []);

  const handleUnpin = (event, id) => {
    event.preventDefault();
    event.stopPropagation();
    setPinnedIds(togglePinnedToolId(id));
  };

  const visibleRegistry = useMemo(
    () => registry.filter((entry) => filteredModuleIds.has(entry.moduleId)),
    [registry, filteredModuleIds],
  );

  const pinnedEntries = pinnedIds
    .map((id) => visibleRegistry.find((e) => e.id === id))
    .filter(Boolean);

  const recentEntries = recents
    .map((r) => visibleRegistry.find((e) => e.id === r.toolId))
    .filter((entry, index, arr) => entry && arr.findIndex((e) => e.id === entry.id) === index)
    .slice(0, 5);

  const groupedByTag = useMemo(() => {
    const groups = {};
    visibleRegistry.forEach((entry) => {
      entry.tags.forEach((tag) => {
        if (!groups[tag]) groups[tag] = [];
        groups[tag].push(entry);
      });
    });
    return groups;
  }, [visibleRegistry]);

  const renderRow = (entry, index, { showUnpin = false } = {}) => (
    <ListItemButton
      key={entry.id}
      component={Link}
      to={entry.path}
      selected={location.pathname.startsWith(entry.path)}
      sx={{
        borderRadius: 1,
        mb: 0.5,
        justifyContent: sidebarOpen ? 'flex-start' : 'center',
        px: sidebarOpen ? 2 : 0,
        '&:hover .unpin-button': { opacity: 1 },
      }}
    >
      <Tooltip title={sidebarOpen ? '' : entry.label} placement="right">
        <ListItemIcon sx={{ minWidth: sidebarOpen ? 36 : 'auto', justifyContent: 'center' }}>
          {entry.icon}
        </ListItemIcon>
      </Tooltip>
      {sidebarOpen && <ListItemText primary={entry.label} />}
      {sidebarOpen && showUnpin ? (
        <Tooltip title={t('leftPanel.unpin')}>
          <IconButton
            className="unpin-button"
            size="small"
            onClick={(e) => handleUnpin(e, entry.id)}
            aria-label={t('leftPanel.unpinAria', { label: entry.label })}
            sx={{ opacity: 0, transition: 'opacity 0.15s', ml: 0.5 }}
          >
            <PushPinIcon fontSize="inherit" />
          </IconButton>
        </Tooltip>
      ) : (
        sidebarOpen && index !== undefined && index < 9 && (
          <Chip label={index + 1} size="small" variant="outlined" sx={{ height: 18, fontSize: '0.65rem' }} />
        )
      )}
    </ListItemButton>
  );

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', px: sidebarOpen ? 1 : 0, py: 1 }}>
      {pinnedEntries.length > 0 && (
        <List
          dense
          subheader={sidebarOpen ? (
            <ListSubheader disableSticky>{t('leftPanel.pinned')}</ListSubheader>
          ) : null}
        >
          {pinnedEntries.map((entry, i) => renderRow(entry, i, { showUnpin: true }))}
        </List>
      )}

      {sidebarOpen && recentEntries.length > 0 && (
        <List dense subheader={<ListSubheader disableSticky>{t('leftPanel.recent')}</ListSubheader>}>
          {recentEntries.map((entry) => renderRow(entry))}
        </List>
      )}

      {Object.keys(groupedByTag).sort().map((tag) => (
        <List
          key={tag}
          dense
          subheader={sidebarOpen ? <ListSubheader disableSticky>{`#${tag}`}</ListSubheader> : null}
        >
          {groupedByTag[tag].map((entry) => renderRow(entry))}
        </List>
      ))}
    </Box>
  );
}
