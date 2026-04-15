import React, { useState, useMemo } from "react";
import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import { Link, useLocation } from "react-router-dom";
import PropTypes from "prop-types";
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';

export default function SidebarTabs({ title, tabs, sidebarOpen }) {
  const location = useLocation();
  const [openItems, setOpenItems] = useState({});

  const activeParents = useMemo(() => {
    const active = {};
    tabs.forEach(tab => {
      if (tab.children?.some(c => location.pathname === c.path)) {
        active[tab.label] = true;
      }
    });
    return active;
  }, [location.pathname, tabs]);

  const handleClick = label => {
    setOpenItems(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const renderTab = (tab, depth = 0) => {
    const isActive    = location.pathname === tab.path;
    const hasChildren = Array.isArray(tab.children) && tab.children.length > 0;
    const isOpen      = openItems[tab.label] || activeParents[tab.label];

    return (
      <React.Fragment key={tab.path}>
        <ListItemButton
          component={Link}
          to={tab.path}
          onClick={hasChildren ? e => {
            e.preventDefault();
            handleClick(tab.label);
          } : undefined}
          selected={isActive}
          sx={{
            width: sidebarOpen ? '95%' : '40px',
            borderRadius: 1,
            mb: 0.5,

            pl: sidebarOpen ? 1 + depth * 2 : 0,
            pr: sidebarOpen ? 2 : 0,
            justifyContent: sidebarOpen ? 'flex-start' : 'center',

            bgcolor: isActive ? 'primary.main' : 'transparent',
            color:   isActive ? 'primary.contrastText' : 'text.primary',
            '&:hover': {
              bgcolor: isActive ? 'primary.dark' : 'action.hover',
            },
          }}
        >
          <ListItemIcon
            sx={{
              color: 'inherit',
              minWidth: 0,
              mr: sidebarOpen ? 2 : 0,
              justifyContent: 'center',
            }}
          >
            {tab.icon}
          </ListItemIcon>

          <ListItemText
            primary={tab.label}
            sx={{ display: sidebarOpen ? 'block' : 'none' }}
          />

          {hasChildren && sidebarOpen && (isOpen ? <ExpandLess /> : <ExpandMore />)}
        </ListItemButton>

        {hasChildren && (
          <Collapse in={isOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {tab.children.map(child => (
                <ListItemButton
                  key={child.path}
                  component={Link}
                  to={child.path}
                  selected={location.pathname === child.path}
                  sx={{
                    pl: sidebarOpen ? 1 + (depth + 1) * 2 : 0,
                    pr: sidebarOpen ? 2 : 0,
                    justifyContent: sidebarOpen ? 'flex-start' : 'center',

                    py: 0.5,
                    borderRadius: 0,
                    bgcolor: 'transparent',

                    borderLeft: sidebarOpen ? '1px solid' : 'none',
                    borderColor: 'divider',

                    '&.Mui-selected': {
                      bgcolor: 'transparent',
                      color: 'primary.main',
                      borderColor: 'primary.main',
                    },
                    '&:hover': {
                      bgcolor: 'transparent',
                      color: 'primary.main',
                    },

                    fontSize: '0.875rem',
                  }}
                >
                  <ListItemText
                    primary={child.label}
                    primaryTypographyProps={{
                      fontSize: '0.875rem',
                      fontWeight: location.pathname === child.path ? 500 : 400,
                    }}
                    sx={{
                      m: 0,
                      display: sidebarOpen ? 'block' : 'none',
                    }}
                  />
                </ListItemButton>
              ))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  return (
    <Box sx={{ p: 1 }}>
      {sidebarOpen && (
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
      )}

      {/* no default padding + center when closed */}
      <List
        disablePadding
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: sidebarOpen ? 'stretch' : 'center',
        }}
      >
        {tabs.map(tab => renderTab(tab))}
      </List>
    </Box>
  );
}

SidebarTabs.propTypes = {
  title: PropTypes.string.isRequired,
  tabs:  PropTypes.array.isRequired,
  sidebarOpen: PropTypes.bool.isRequired,
};
