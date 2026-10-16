import { Link, useLocation } from 'react-router';
import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import { findActiveTabPath } from '../../utils/activeTab';

/**
 * Horizontal sub-navigation above a feature's page — used for flat tab sets (New / History /
 * Settings), which don't justify a whole second side column. Tab sets with nested children
 * (Newsfeed's settings group) stay in the SidebarTabs drawer instead; see Layout.jsx.
 */
export default function FeatureTabs({ tabs }) {
  const location = useLocation();

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
      <Tabs
        value={findActiveTabPath(tabs, location.pathname)}
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
      >
        {tabs.map((tab) => (
          <Tab
            key={tab.path}
            value={tab.path}
            label={tab.label}
            icon={tab.icon}
            iconPosition="start"
            component={Link}
            to={tab.path}
            sx={{ minHeight: 48 }}
          />
        ))}
      </Tabs>
    </Box>
  );
}
