import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

/** One "label: value" line of a result panel; renders nothing for an empty value. */
export default function FieldRow({ label, value }) {
  if (!value) return null;
  return (
    <Box sx={{ display: 'flex', gap: 1, mb: 0.5 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 200 }}>{label}</Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}
