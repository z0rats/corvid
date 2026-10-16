import { useState, useMemo, useRef, useEffect } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { hasLlmKeyAtom, themeModeAtom } from '../../state/atoms';
import { useVisibleModuleIds } from '../../hooks/useVisibleModuleIds';
import { useThemeManager } from '../../hooks/ui/useThemeManager';
import { usePersistentState } from '../../hooks/ui/usePersistentState';
import { Outlet, Link, useLocation } from 'react-router';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import SettingsIcon from '@mui/icons-material/Settings';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import SearchIcon from '@mui/icons-material/SearchOutlined';
import HomeIcon from '@mui/icons-material/HomeOutlined';
import SidebarTabs from '../ui/SidebarTabs';
import FeatureTabs from '../ui/FeatureTabs';
import LeftPanel from './LeftPanel';
import ResizeHandle from './ResizeHandle';
import CommandPalette from '../ui/CommandPalette/CommandPalette';
import AlertsMenu from '../ui/AlertsMenu';
import ActiveScansMenu from '../ui/ActiveScansMenu';
import { OPEN_COMMAND_PALETTE_EVENT } from '../../hooks/useGlobalPaletteShortcuts';
import { TAB_ROUTES } from '../../config/sidebarConfig';
import { useTheme, alpha } from '@mui/material/styles';

const defaultDrawerWidth = 240;
const minDrawerWidth = 180;
const maxDrawerWidth = 480;
const miniDrawerWidth = 60;
const defaultLeftPanelWidth = 220;
const minLeftPanelWidth = 160;
const maxLeftPanelWidth = 360;
const leftPanelMiniWidth = 56;

const isBoolean = (value) => typeof value === 'boolean';
const isWidthBetween = (min, max) => (value) => Number.isFinite(value) && value >= min && value <= max;

/**
 * Main layout component that provides the application structure
 */
function Layout() {
  const { t } = useTranslation();
  const { t: tPalette } = useTranslation('commandPalette');
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);
  const themeMode = useAtomValue(themeModeAtom);
  const { toggleColorMode } = useThemeManager();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = usePersistentState('layout.sidebarOpen', true, isBoolean);
  const [sidebarWidth, setSidebarWidth] = usePersistentState(
    'layout.sidebarWidth', defaultDrawerWidth, isWidthBetween(minDrawerWidth, maxDrawerWidth),
  );
  const [leftPanelOpen, setLeftPanelOpen] = usePersistentState('layout.leftPanelOpen', true, isBoolean);
  const [leftPanelWidth, setLeftPanelWidth] = usePersistentState(
    'layout.leftPanelWidth', defaultLeftPanelWidth, isWidthBetween(minLeftPanelWidth, maxLeftPanelWidth),
  );
  // Tracks which panel ('leftPanel' | 'sidebar') is being dragged, not just whether — a ref since
  // it drives a synchronous pointermove listener, not a render.
  const resizingPanel = useRef(null);
  const resizeStartX = useRef(0);
  const resizeStartWidth = useRef(0);
  const location = useLocation();
  const theme = useTheme();

  const handleDrawerToggle = () => setMobileOpen(prev => !prev);
  const handleSidebarToggle = () => setSidebarOpen(prev => !prev);
  const handleLeftPanelToggle = () => setLeftPanelOpen(prev => !prev);
  const handleOpenPalette = () => window.dispatchEvent(new Event(OPEN_COMMAND_PALETTE_EVENT));

  // Drag delta from the pointer's start position, not the pointer's absolute X — the drawer this
  // handle sits on isn't flush against the viewport's left edge (the sidebar drawer starts after
  // the left panel's width), so using e.clientX directly as the new width previously ignored that
  // offset and made the panel jump to (roughly) the cursor's raw X on the very first move.
  const startResize = (panel) => (e) => {
    e.preventDefault();
    resizingPanel.current = panel;
    resizeStartX.current = e.clientX;
    resizeStartWidth.current = panel === 'leftPanel' ? leftPanelWidth : sidebarWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  useEffect(() => {
    const handlePointerMove = (e) => {
      const panel = resizingPanel.current;
      if (!panel) return;
      const newWidth = resizeStartWidth.current + (e.clientX - resizeStartX.current);
      if (panel === 'leftPanel') {
        setLeftPanelWidth(Math.min(maxLeftPanelWidth, Math.max(minLeftPanelWidth, newWidth)));
      } else {
        setSidebarWidth(Math.min(maxDrawerWidth, Math.max(minDrawerWidth, newWidth)));
      }
    };

    const handlePointerUp = () => {
      if (!resizingPanel.current) return;
      resizingPanel.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('pointermove', handlePointerMove);
    document.addEventListener('pointerup', handlePointerUp);
    document.addEventListener('pointercancel', handlePointerUp);
    return () => {
      document.removeEventListener('pointermove', handlePointerMove);
      document.removeEventListener('pointerup', handlePointerUp);
      document.removeEventListener('pointercancel', handlePointerUp);
    };
  }, [setLeftPanelWidth, setSidebarWidth]);

  const currentTabs = useMemo(() => {
    const route = TAB_ROUTES.find(({ prefix }) => location.pathname.startsWith(prefix));
    return route ? route.getTabs(t, { hasLlmKey }) : null;
  }, [location.pathname, hasLlmKey, t]);

  const filteredModuleIds = useVisibleModuleIds();

  // Only a tab set with nested children (Newsfeed's settings group) gets the side drawer; a flat
  // one renders as FeatureTabs above the page, so a 2-3 tab feature doesn't cost a whole column.
  const showSidebar = Boolean(currentTabs?.some((tab) => tab.children?.length));
  const showFeatureTabs = Boolean(currentTabs) && !showSidebar;

  const leftPanelFooterContent = (
    <Box
      sx={{
        px: leftPanelOpen ? 2 : 0,
        py: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: leftPanelOpen ? 'flex-end' : 'center',
        minHeight: 56,
      }}
    >
      <IconButton onClick={handleLeftPanelToggle} aria-label={t('layout.toggleSidebar')}>
        {leftPanelOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
      </IconButton>
    </Box>
  );

  const leftPanelDrawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
        <LeftPanel sidebarOpen={leftPanelOpen} filteredModuleIds={filteredModuleIds} />
      </Box>
      <Divider />
      {leftPanelFooterContent}
    </Box>
  );

  const sidebarFooterContent = (
    <Box
      sx={{
        px: sidebarOpen ? 2 : 0,
        py: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: sidebarOpen ? 'flex-end' : 'center',
        minHeight: 56,
      }}
    >
      <IconButton onClick={handleSidebarToggle} aria-label={t('layout.toggleSidebar')}>
        {sidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
      </IconButton>
    </Box>
  );

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
        {currentTabs && <SidebarTabs title="" tabs={currentTabs} sidebarOpen={sidebarOpen} />}
      </Box>
      <Divider />
      {sidebarFooterContent}
    </Box>
  );

  const mobileDrawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflowY: 'auto' }} onClick={(e) => {
        // Close the mobile drawer after navigating via a LeftPanel/SidebarTabs link tap.
        if (e.target.closest('a')) handleDrawerToggle();
      }}
      >
        <LeftPanel sidebarOpen filteredModuleIds={filteredModuleIds} />
        {showSidebar && (
          <>
            <Divider sx={{ mx: 1 }} />
            <SidebarTabs title="" tabs={currentTabs} sidebarOpen={true} />
          </>
        )}
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar sx={{ minHeight: '56px !important', height: '56px' }}>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            aria-label={t('layout.openMenu')}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Tooltip title={t('layout.home')}>
            <IconButton
              color="inherit"
              component={Link}
              to="/"
              aria-label={t('layout.home')}
              sx={{ mr: 0.5 }}
            >
              <HomeIcon />
            </IconButton>
          </Tooltip>
          <Typography
            component={Link}
            to="/"
            variant="subtitle1"
            sx={{
              display: { xs: 'none', sm: 'block' },
              color: 'inherit',
              textDecoration: 'none',
              fontWeight: 600,
              letterSpacing: '0.04em',
              mr: 1,
            }}
          >
            Corvid
          </Typography>

          {location.pathname === '/' ? (
            // StartScreen (rendered below, at "/") already is a live search input with the same
            // placeholder - showing this trigger too would just be a second, confusingly identical
            // search box stacked right above it. Keep the flex spacer so the right-side icons stay put.
            <Box sx={{ flexGrow: 1 }} />
          ) : (
            <Box
              onClick={handleOpenPalette}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleOpenPalette(); }}
              aria-label={tPalette('searchPlaceholder')}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                flexGrow: 1,
                mx: 2,
                maxWidth: 480,
                px: 2,
                py: 0.75,
                borderRadius: 2,
                bgcolor: alpha(theme.palette.common.white, 0.15),
                color: 'inherit',
                cursor: 'pointer',
                '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.25) },
              }}
            >
              <SearchIcon fontSize="small" />
              <Typography variant="body2" noWrap sx={{ opacity: 0.85, flexGrow: 1 }}>
                {tPalette('searchPlaceholder')}
              </Typography>
              <Chip
                label="/"
                size="small"
                variant="outlined"
                sx={{
                  display: { xs: 'none', sm: 'flex' },
                  color: 'inherit',
                  borderColor: alpha(theme.palette.common.white, 0.4),
                  fontFamily: 'monospace',
                }}
              />
            </Box>
          )}

          <Box sx={{ display: 'flex', alignItems: 'center', ml: 'auto', flexShrink: 0, pl: 2 }}>
            <ActiveScansMenu />
            <AlertsMenu />
            <Tooltip title={themeMode === 'dark' ? t('layout.switchToLightMode') : t('layout.switchToDarkMode')}>
              <IconButton color="inherit" onClick={toggleColorMode} aria-label={t('layout.toggleDarkMode')}>
                {themeMode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
              </IconButton>
            </Tooltip>
            <Tooltip title={t('layout.settings')}>
              <IconButton
                color="inherit"
                component={Link}
                to="/settings"
                aria-label={t('layout.settings')}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        open={leftPanelOpen}
        sx={{
          display: { xs: 'none', md: 'block' },
          flexShrink: 0,
          whiteSpace: 'nowrap',
          width: leftPanelOpen ? leftPanelWidth : leftPanelMiniWidth,
          transition: resizingPanel.current === 'leftPanel'
            ? 'none'
            : theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            top: '56px',
            left: 0,
            height: 'calc(100vh - 56px)',
            width: leftPanelOpen ? leftPanelWidth : leftPanelMiniWidth,
            overflowX: 'hidden',
            transition: resizingPanel.current === 'leftPanel'
              ? 'none'
              : theme.transitions.create('width', {
                  easing: theme.transitions.easing.sharp,
                  duration: leftPanelOpen
                    ? theme.transitions.duration.enteringScreen
                    : theme.transitions.duration.leavingScreen,
                }),
          },
        }}
      >
        {leftPanelDrawerContent}
        {leftPanelOpen && (
          <ResizeHandle
            label={t('layout.resizeToolPanel')}
            value={leftPanelWidth}
            min={minLeftPanelWidth}
            max={maxLeftPanelWidth}
            onPointerDown={startResize('leftPanel')}
            onChange={setLeftPanelWidth}
          />
        )}
      </Drawer>

      {showSidebar && (
        <Drawer
          variant="permanent"
          open={sidebarOpen}
          sx={{
            display: { xs: 'none', md: 'block' },
            flexShrink: 0,
            whiteSpace: 'nowrap',
            width: sidebarOpen ? sidebarWidth : miniDrawerWidth,
            transition: resizingPanel.current === 'sidebar'
              ? 'none'
              : theme.transitions.create('width', {
                  easing: theme.transitions.easing.sharp,
                  duration: theme.transitions.duration.enteringScreen,
                }),
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              top: '56px',
              left: leftPanelOpen ? leftPanelWidth : leftPanelMiniWidth,
              height: 'calc(100vh - 56px)',
              width: sidebarOpen ? sidebarWidth : miniDrawerWidth,
              overflowX: 'hidden',
              transition: resizingPanel.current === 'sidebar'
                ? 'none'
                : theme.transitions.create('width', {
                    easing: theme.transitions.easing.sharp,
                    duration: sidebarOpen
                      ? theme.transitions.duration.enteringScreen
                      : theme.transitions.duration.leavingScreen,
                  }),
            },
          }}
        >
          {drawerContent}
          {sidebarOpen && (
            <ResizeHandle
              label={t('layout.resizeSectionPanel')}
              value={sidebarWidth}
              min={minDrawerWidth}
              max={maxDrawerWidth}
              onPointerDown={startResize('sidebar')}
              onChange={setSidebarWidth}
            />
          )}
        </Drawer>
      )}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: defaultDrawerWidth,
            boxSizing: 'border-box',
            top: '56px',
            height: 'calc(100vh - 56px)',
          },
        }}
      >
        {mobileDrawerContent}
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          p: 2,
        }}
      >
        <Toolbar />
        {showFeatureTabs && <FeatureTabs tabs={currentTabs} />}
        <Outlet />
      </Box>

      <CommandPalette />
    </Box>
  );
}

export default Layout;
