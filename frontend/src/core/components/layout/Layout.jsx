import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useAtomValue } from 'jotai';
import { hasLlmKeyAtom, enabledModulesMapAtom, themeModeAtom } from '../../state/atoms';
import { useThemeManager } from '../../hooks/ui/useThemeManager';
import { Outlet, Link, useLocation } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import SettingsIcon from '@mui/icons-material/Settings';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import SidebarTabs from '../ui/SidebarTabs';
import {
  mainMenuItems,
  aiTemplatesTabs,
  newsfeedTabs,
  settingsTabs,
  rulesTabs,
  iocToolsTabs,
  cvssTabs,
} from '../../config/sidebarConfig';
import ot_logo_dark from '../../static/images/ot_logo_dark.png';
import { useTheme, alpha } from '@mui/material/styles';

const defaultDrawerWidth = 240;
const minDrawerWidth = 180;
const maxDrawerWidth = 480;
const miniDrawerWidth = 60;

const menuItems = mainMenuItems;

/**
 * Main layout component that provides the application structure
 */
function Layout() {
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);
  const enabledModules = useAtomValue(enabledModulesMapAtom);
  const themeMode = useAtomValue(themeModeAtom);
  const { toggleColorMode } = useThemeManager();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(defaultDrawerWidth);
  const isResizing = useRef(false);
  const location = useLocation();
  const theme = useTheme();

  const handleDrawerToggle = () => setMobileOpen(prev => !prev);
  const handleSidebarToggle = () => setSidebarOpen(prev => !prev);

  const handleResizeStart = useCallback((e) => {
    e.preventDefault();
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing.current) return;
      const newWidth = Math.min(maxDrawerWidth, Math.max(minDrawerWidth, e.clientX));
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (!isResizing.current) return;
      isResizing.current = false;
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
    if (location.pathname.startsWith('/ai-templates') && hasLlmKey) return aiTemplatesTabs;
    if (location.pathname.startsWith('/newsfeed')) {
      return newsfeedTabs.filter(tab => tab.path !== '/newsfeed/report' || hasLlmKey);
    }
    if (location.pathname.startsWith('/settings')) return settingsTabs;
    if (location.pathname.startsWith('/rules')) return rulesTabs;
    if (location.pathname.startsWith('/ioc-tools')) return iocToolsTabs;
    if (location.pathname.startsWith('/cvss-calculator')) return cvssTabs;
    return null;
  }, [location.pathname, hasLlmKey]);

  const filteredMenuItems = useMemo(() => menuItems.filter(item => {
    if (item.moduleId === 'llm_templates') {
      return hasLlmKey && (enabledModules[item.moduleId] ?? true);
    }
    return enabledModules[item.moduleId] ?? true;
  }), [hasLlmKey, enabledModules]);

  const showSidebar = Boolean(currentTabs);

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
      <IconButton onClick={handleSidebarToggle} aria-label="Toggle sidebar">
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
      <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
        <Box sx={{ p: 1 }}>
          <List disablePadding>
            {filteredMenuItems.map((item) => (
              <ListItemButton
                key={item.path}
                component={Link}
                to={item.path}
                onClick={handleDrawerToggle}
                selected={location.pathname.startsWith(item.path)}
                sx={{
                  borderRadius: 1,
                  mb: 0.5,
                  bgcolor: location.pathname.startsWith(item.path)
                    ? 'primary.main'
                    : 'transparent',
                  color: location.pathname.startsWith(item.path)
                    ? 'primary.contrastText'
                    : 'text.primary',
                  '&:hover': {
                    bgcolor: location.pathname.startsWith(item.path)
                      ? 'primary.dark'
                      : 'action.hover',
                  },
                }}
              >
                <ListItemIcon sx={{ color: 'inherit', minWidth: 0, mr: 2 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.name} />
              </ListItemButton>
            ))}
          </List>
        </Box>
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
            aria-label="Open menu"
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Box component="img" src={ot_logo_dark} alt="Logo" sx={{ height: 36, mr: 2 }} />

          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              flexGrow: 1,
              ml: 2,
            }}
          >
            {filteredMenuItems.map((item, idx) => (
              <Button
                key={item.path}
                component={Link}
                to={item.path}
                color="inherit"
                startIcon={item.icon}
                sx={{
                  ml: idx === 0 ? 0 : 2,
                  bgcolor: location.pathname.startsWith(item.path)
                    ? alpha(theme.palette.common.white, 0.2)
                    : 'transparent',
                  '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.3) },
                }}
              >
                {item.name}
              </Button>
            ))}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', ml: 'auto' }}>
            <Tooltip title={themeMode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
              <IconButton color="inherit" onClick={toggleColorMode} aria-label="Toggle dark mode">
                {themeMode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Settings">
              <IconButton
                color="inherit"
                component={Link}
                to="/settings"
                aria-label="Settings"
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      {showSidebar && (
        <Drawer
          variant="permanent"
          open={sidebarOpen}
          sx={{
            display: { xs: 'none', md: 'block' },
            flexShrink: 0,
            whiteSpace: 'nowrap',
            width: sidebarOpen ? sidebarWidth : miniDrawerWidth,
            transition: isResizing.current
              ? 'none'
              : theme.transitions.create('width', {
                  easing: theme.transitions.easing.sharp,
                  duration: theme.transitions.duration.enteringScreen,
                }),
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              top: '56px',
              height: 'calc(100vh - 56px)',
              width: sidebarOpen ? sidebarWidth : miniDrawerWidth,
              overflowX: 'hidden',
              transition: isResizing.current
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
              onMouseDown={handleResizeStart}
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
    </Box>
  );
}

export default Layout;
