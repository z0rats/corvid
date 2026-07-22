import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useNavigate } from 'react-router-dom';

/**
 * Touch fallback for the result list — renders as a tile grid instead of a keyboard-navigable
 * list. Auto-switches on `@media (pointer: coarse)` or the "Always tiles" setting; same result
 * set, different layout (see docs/command-palette-plan.md's Touch fallback section).
 */
export default function TileGrid({ registry, onOpen }) {
  const navigate = useNavigate();

  const handleClick = (entry) => {
    if (onOpen) onOpen(entry);
    else navigate(entry.path);
  };

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
        gap: 1.5,
        p: 2,
      }}
    >
      {registry.map((entry) => (
        <Paper
          key={entry.id}
          elevation={0}
          onClick={() => handleClick(entry)}
          sx={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            gap: 1, p: 2, cursor: 'pointer', border: '1px solid', borderColor: 'divider', borderRadius: 2,
            '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' },
          }}
        >
          <Box sx={{ fontSize: 28, color: 'primary.main', display: 'flex' }}>{entry.icon}</Box>
          <Typography variant="body2" align="center">{entry.label}</Typography>
        </Paper>
      ))}
    </Box>
  );
}
