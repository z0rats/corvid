import { useCallback, useLayoutEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import { alpha, useTheme } from '@mui/material/styles';

const ITEM_GAP = 8;
const MORE_BUTTON_RESERVED_WIDTH = 100;

/**
 * Top app bar navigation that fits as many items as the available width
 * allows and collapses the rest into a "More" menu, instead of clipping
 * or wrapping items off-screen.
 */
export default function TopNavMenu({ items, isActive }) {
  const theme = useTheme();
  const { t } = useTranslation();
  const containerRef = useRef(null);
  const measureRefs = useRef([]);
  const [visibleCount, setVisibleCount] = useState(items.length);
  const [anchorEl, setAnchorEl] = useState(null);

  const recalculate = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const containerWidth = container.offsetWidth;
    const widths = measureRefs.current.map((el) => (el ? el.offsetWidth : 0));

    let used = 0;
    let count = 0;
    for (let i = 0; i < widths.length; i++) {
      const isLast = i === widths.length - 1;
      const reserve = isLast ? 0 : MORE_BUTTON_RESERVED_WIDTH;
      used += widths[i] + (i > 0 ? ITEM_GAP : 0);
      if (used + reserve > containerWidth) break;
      count = i + 1;
    }
    setVisibleCount(count);
  }, []);

  useLayoutEffect(() => {
    recalculate();
    const container = containerRef.current;
    if (!container || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(recalculate);
    observer.observe(container);
    return () => observer.disconnect();
  }, [recalculate, items]);

  const visibleItems = items.slice(0, visibleCount);
  const overflowItems = items.slice(visibleCount);
  const overflowHasActive = overflowItems.some((item) => isActive(item.path));

  const handleMoreClick = (e) => setAnchorEl(e.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const itemButtonSx = (item, idx) => ({
    ml: idx === 0 ? 0 : 1,
    flexShrink: 0,
    whiteSpace: 'nowrap',
    bgcolor: isActive(item.path) ? alpha(theme.palette.common.white, 0.2) : 'transparent',
    '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.3) },
  });

  return (
    <Box
      ref={containerRef}
      sx={{
        display: { xs: 'none', md: 'flex' },
        flexGrow: 1,
        flexShrink: 1,
        minWidth: 0,
        ml: 2,
        position: 'relative',
      }}
    >
      {/* Off-screen measurement row: real widths of all items at natural size */}
      <Box sx={{ position: 'absolute', top: -9999, left: 0, display: 'flex', visibility: 'hidden', pointerEvents: 'none' }}>
        {items.map((item, idx) => (
          <Button
            key={item.path}
            ref={(el) => { measureRefs.current[idx] = el; }}
            startIcon={item.icon}
            sx={{ ml: idx === 0 ? 0 : 1, whiteSpace: 'nowrap' }}
          >
            {item.name}
          </Button>
        ))}
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', overflow: 'hidden' }}>
        {visibleItems.map((item, idx) => (
          <Button
            key={item.path}
            component={Link}
            to={item.path}
            color="inherit"
            startIcon={item.icon}
            sx={itemButtonSx(item, idx)}
          >
            {item.name}
          </Button>
        ))}

        {overflowItems.length > 0 && (
          <>
            <Button
              color="inherit"
              onClick={handleMoreClick}
              endIcon={<MoreHorizIcon />}
              sx={{
                ml: visibleItems.length > 0 ? 1 : 0,
                flexShrink: 0,
                whiteSpace: 'nowrap',
                bgcolor: overflowHasActive ? alpha(theme.palette.common.white, 0.2) : 'transparent',
                '&:hover': { bgcolor: alpha(theme.palette.common.white, 0.3) },
              }}
            >
              {t('layout.more')}
            </Button>
            <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
              {overflowItems.map((item) => (
                <MenuItem
                  key={item.path}
                  component={Link}
                  to={item.path}
                  selected={isActive(item.path)}
                  onClick={handleMenuClose}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText>{item.name}</ListItemText>
                </MenuItem>
              ))}
            </Menu>
          </>
        )}
      </Box>
    </Box>
  );
}
