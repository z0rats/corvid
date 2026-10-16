import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation } from 'react-router';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListSubheader from '@mui/material/ListSubheader';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import PushPinIcon from '@mui/icons-material/PushPin';
import { buildCommandRegistry } from '../../config/commandRegistry';
import { SECTION_ORDER } from '../../config/sidebarConfig';
import { getPinnedToolIds, togglePinnedToolId, PINNED_CHANGED_EVENT } from '../../utils/commandPaletteStorage';

/**
 * Global tool catalog — replaces both TopNavMenu (top bar) and the mobile drawer's flat tool
 * list (see docs/architecture/command-palette.md). Renders leftmost, with the
 * existing per-feature sub-tab Drawer (SidebarTabs) unchanged immediately to its right when a
 * feature has sub-tabs — confirmed as two stacked panels rather than one replacing the other.
 */
export default function LeftPanel({ sidebarOpen, filteredModuleIds }) {
  const { t } = useTranslation('commandPalette');
  // sidebarConfig.jsx's i18nKeys (nav.*) live in the default 'common' namespace.
  const { t: tCommon } = useTranslation();
  const location = useLocation();
  const [pinnedIds, setPinnedIds] = useState(getPinnedToolIds);

  const registry = useMemo(() => buildCommandRegistry(tCommon), [tCommon]);

  useEffect(() => {
    // Storage is written synchronously by the palette before it navigates, so re-reading on
    // every route change picks up palette-driven pins without a shared store.
    setPinnedIds(getPinnedToolIds());
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

  const sections = useMemo(
    () => SECTION_ORDER
      .map((section) => ({ section, entries: visibleRegistry.filter((entry) => entry.section === section) }))
      .filter(({ entries }) => entries.length > 0),
    [visibleRegistry],
  );

  // Recents deliberately aren't listed here - the start screen and the palette already surface
  // them, and a third copy of the same tool in this panel only added noise. A pinned row is a
  // shortcut, so only the tool's own section row shows the active highlight, not both.
  const renderRow = (entry, { pinned = false } = {}) => (
    <ListItemButton
      key={entry.id}
      component={Link}
      to={entry.path}
      selected={!pinned && location.pathname.startsWith(entry.path)}
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
      {sidebarOpen && (
        <ListItemText primary={entry.label} slotProps={{ primary: { noWrap: true, title: entry.label } }} />
      )}
      {sidebarOpen && pinned && (
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
          {pinnedEntries.map((entry) => renderRow(entry, { pinned: true }))}
        </List>
      )}

      {sections.map(({ section, entries }, index) => (
        <List
          key={section}
          dense
          subheader={sidebarOpen
            ? <ListSubheader disableSticky>{t(`leftPanel.sections.${section}`)}</ListSubheader>
            // Collapsed: no headings fit, so a divider keeps the groups visually apart.
            : (index > 0 || pinnedEntries.length > 0) && <Divider sx={{ mx: 1, mb: 0.5 }} />}
        >
          {entries.map((entry) => renderRow(entry))}
        </List>
      ))}
    </Box>
  );
}
