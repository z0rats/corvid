import { useState, useMemo, useRef, useEffect } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import { hasLlmKeyAtom, enabledModulesMapAtom, themeModeAtom, generalSettingsState } from '../../state/atoms';
import { useThemeManager } from '../../hooks/ui/useThemeManager';
import { useGeneralSettings } from '../../../features/settings/hooks/api/useGeneralSettings';
import { Outlet, Link, useLocation } from 'react-router-dom';
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
import LeftPanel from './LeftPanel';
import CommandPalette from '../ui/CommandPalette/CommandPalette';
import { OPEN_COMMAND_PALETTE_EVENT } from '../../hooks/useCommandPalette';
import {
  getMainMenuItems,
  getAiTemplatesTabs,
  getNewsfeedTabs,
  getSettingsTabs,
  getRulesTabs,
  getIocToolsTabs,
  getCvssTabs,
  getUsernameSearchTabs,
  getEmailSearchTabs,
  getRedditSearchTabs,
  getGitReconTabs,
} from '../../config/sidebarConfig';
import { useTheme, alpha } from '@mui/material/styles';

const defaultDrawerWidth = 240;
const minDrawerWidth = 180;
const maxDrawerWidth = 480;
const miniDrawerWidth = 60;
const defaultLeftPanelWidth = 220;
const minLeftPanelWidth = 160;
const maxLeftPanelWidth = 360;
const leftPanelMiniWidth = 56;

/**
 * Main layout component that provides the application structure
 */
function Layout() {
  const { t } = useTranslation();
  const { t: tPalette } = useTranslation('commandPalette');
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);
  const enabledModules = useAtomValue(enabledModulesMapAtom);
  const themeMode = useAtomValue(themeModeAtom);
  const { toggleColorMode } = useThemeManager();
  const generalSettings = useAtomValue(generalSettingsState);
  const { updateLanguage } = useGeneralSettings();
  const currentLanguage = generalSettings?.language || 'en';
  const handleLanguageToggle = () => updateLanguage(currentLanguage === 'en' ? 'ru' : 'en');
  const menuItems = useMemo(() => getMainMenuItems(t), [t]);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(defaultDrawerWidth);
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [leftPanelWidth, setLeftPanelWidth] = useState(defaultLeftPanelWidth);
  // Tracks which panel ('leftPanel' | 'sidebar') is being dragged, not just whether — a ref since
  // it drives a synchronous mousemove listener, not a render.
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
    const handleMouseMove = (e) => {
      const panel = resizingPanel.current;
      if (!panel) return;
      const newWidth = resizeStartWidth.current + (e.clientX - resizeStartX.current);
      if (panel === 'leftPanel') {
        setLeftPanelWidth(Math.min(maxLeftPanelWidth, Math.max(minLeftPanelWidth, newWidth)));
      } else {
        setSidebarWidth(Math.min(maxDrawerWidth, Math.max(minDrawerWidth, newWidth)));
      }
    };

    const handleMouseUp = () => {
      if (!resizingPanel.current) return;
      resizingPanel.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const currentTabs = useMemo(() => {
    if (location.pathname.startsWith('/ai-templates') && hasLlmKey) return getAiTemplatesTabs(t);
    if (location.pathname.startsWith('/newsfeed')) {
      return getNewsfeedTabs(t).filter(tab => tab.path !== '/newsfeed/report' || hasLlmKey);
    }
    if (location.pathname.startsWith('/settings')) return getSettingsTabs(t);
    if (location.pathname.startsWith('/rules')) return getRulesTabs(t);
    if (location.pathname.startsWith('/ioc-tools')) return getIocToolsTabs(t);
    if (location.pathname.startsWith('/cvss-calculator')) return getCvssTabs(t);
    if (location.pathname.startsWith('/username-search')) return getUsernameSearchTabs(t);
    if (location.pathname.startsWith('/email-search')) return getEmailSearchTabs(t);
    if (location.pathname.startsWith('/reddit-search')) return getRedditSearchTabs(t);
    if (location.pathname.startsWith('/git-recon')) return getGitReconTabs(t);
    return null;
  }, [location.pathname, hasLlmKey, t]);

  const filteredMenuItems = useMemo(() => menuItems.filter(item => {
    if (item.moduleId === 'llm_templates') {
      return hasLlmKey && (enabledModules[item.moduleId] ?? true);
    }
    return enabledModules[item.moduleId] ?? true;
  }), [hasLlmKey, enabledModules, menuItems]);

  const filteredModuleIds = useMemo(
    () => new Set(filteredMenuItems.map(item => item.moduleId)),
    [filteredMenuItems],
  );

  const showSidebar = Boolean(currentTabs);

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
        {currentTabs && (
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
              sx={{ mr: 1 }}
            >
              <HomeIcon />
            </IconButton>
          </Tooltip>

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

          <Box sx={{ display: 'flex', alignItems: 'center', ml: 'auto', flexShrink: 0, pl: 2 }}>
            <Tooltip title={currentLanguage === 'en' ? 'Русский' : 'English'}>
              <IconButton
                color="inherit"
                onClick={handleLanguageToggle}
                aria-label="toggle language"
                sx={{ fontSize: '0.8rem', fontWeight: 600 }}
              >
                {currentLanguage === 'en' ? 'RU' : 'EN'}
              </IconButton>
            </Tooltip>
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
          <Box
            onMouseDown={startResize('leftPanel')}
            sx={{
              position: 'absolute',
              top: 0,
              right: 0,
              bottom: 0,
              width: 6,
              cursor: 'col-resize',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              '&::after': {
                content: '""',
                width: 2,
                height: 32,
                borderRadius: 1,
                bgcolor: 'divider',
                transition: 'background-color 0.2s, height 0.2s',
              },
              '&:hover::after': {
                bgcolor: 'primary.main',
                height: 48,
              },
            }}
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
            <Box
              onMouseDown={startResize('sidebar')}
              sx={{
                position: 'absolute',
                top: 0,
                right: 0,
                bottom: 0,
                width: 6,
                cursor: 'col-resize',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                '&::after': {
                  content: '""',
                  width: 2,
                  height: 32,
                  borderRadius: 1,
                  bgcolor: 'divider',
                  transition: 'background-color 0.2s, height 0.2s',
                },
                '&:hover::after': {
                  bgcolor: 'primary.main',
                  height: 48,
                },
              }}
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
          display: 'flex',
          flexDirection: 'column',
          p: 2,
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>

      <CommandPalette />
    </Box>
  );
}

export default Layout;
