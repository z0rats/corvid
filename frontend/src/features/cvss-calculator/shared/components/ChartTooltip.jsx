import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

export default function ChartTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <Box
        sx={{
          backgroundColor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          p: 1,
          boxShadow: 2,
        }}
      >
        <Typography variant="body2" fontWeight="bold">
          {label}
        </Typography>
        <Typography variant="body2" color="primary">
          Score: {data.normalizedScore.toFixed(2)}/10
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Value: {data.displayValue}
        </Typography>
      </Box>
    );
  }
  return null;
}
