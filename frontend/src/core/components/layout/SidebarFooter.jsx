import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import SettingsIcon from '@mui/icons-material/Settings';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

function SidebarFooter({ themeMode, onToggleColorMode, onSettingsClick }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <IconButton color="inherit" onClick={onToggleColorMode} aria-label="Toggle dark mode">
        {themeMode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
      </IconButton>
      <IconButton
        color="inherit"
        component={Link}
        to="/settings"
        onClick={onSettingsClick}
        aria-label="Settings"
      >
        <SettingsIcon />
      </IconButton>
    </Box>
  );
}

export default SidebarFooter;
