import InfoIcon from '@mui/icons-material/Info';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';

export default function MetricSelect({ label, value, options, onChange, onInfoClick }) {
  return (
    <Box display="flex" alignItems="center" sx={{ my: 2, mx: 4 }}>
      <TextField
        select
        fullWidth
        size="small"
        label={label}
        value={value}
        onChange={onChange}
        slotProps={{
          input: { sx: { borderRadius: "1" } },
        }}
      >
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
      {onInfoClick && (
        <IconButton onClick={onInfoClick} aria-label="Show metric info">
          <InfoIcon />
        </IconButton>
      )}
    </Box>
  );
}
