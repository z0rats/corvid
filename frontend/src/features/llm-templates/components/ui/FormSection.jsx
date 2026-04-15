import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

export default function FormSection({ title, actions, children }) {
  return (
    <Paper sx={{ p: 2.5, mb: 2, borderRadius: 1.5 }} elevation={0}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h6">{title}</Typography>
        {actions}
      </Box>
      <Box mt={2}>{children}</Box>
    </Paper>
  );
}
