import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import ArrowForwardIcon from '@mui/icons-material/ArrowForwardOutlined';

/** Session-only pivot trail (value -> tool -> sent onward). Not persisted. */
export default function Breadcrumbs({ trail }) {
  if (!trail || trail.length === 0) return null;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5, px: 2, py: 1 }}>
      {trail.map((step, index) => (
        <Box key={`${step.toolId}-${index}`} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {index > 0 && <ArrowForwardIcon fontSize="small" sx={{ color: 'text.disabled' }} />}
          <Chip
            label={step.value ? `${step.label} (${step.value})` : step.label}
            size="small"
            variant={step.pending ? 'outlined' : 'filled'}
            sx={{ opacity: step.pending ? 0.5 : 1 }}
          />
        </Box>
      ))}
    </Box>
  );
}
