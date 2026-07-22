import Box from '@mui/material/Box';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import { alpha, useTheme } from '@mui/material/styles';

/** One selectable row in the palette's result list — a registry entry or a which-key suggestion. */
export default function ResultRow({ item, index, isSelected, onSelect, onActionPanel }) {
  const theme = useTheme();
  const jumpKey = index < 9 ? index + 1 : null;

  const label = item.type === 'entry' ? item.entry.label : item.value;
  const icon = item.type === 'entry' ? item.entry.icon : null;

  return (
    <ListItemButton
      selected={isSelected}
      onClick={() => onSelect(index)}
      onContextMenu={(e) => { e.preventDefault(); onActionPanel?.(index); }}
      sx={{
        borderRadius: 1,
        mb: 0.5,
        bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.15) : 'transparent',
      }}
    >
      {icon && <ListItemIcon sx={{ minWidth: 36 }}>{icon}</ListItemIcon>}
      <ListItemText
        primary={label}
        secondary={item.type === 'entry' ? item.entry.tags.join(', ') : null}
      />
      {jumpKey && (
        <Chip
          label={jumpKey}
          size="small"
          variant="outlined"
          sx={{ ml: 1, height: 20, fontSize: '0.7rem', fontFamily: 'monospace' }}
        />
      )}
      {item.type === 'entry' && (
        <Box
          component="button"
          type="button"
          aria-label="Row actions"
          onClick={(e) => { e.stopPropagation(); onActionPanel?.(index); }}
          sx={{
            border: 'none', background: 'none', cursor: 'pointer', color: 'text.secondary',
            fontFamily: 'monospace', fontSize: '0.7rem', ml: 1,
          }}
        >
          ⌘K
        </Box>
      )}
    </ListItemButton>
  );
}
