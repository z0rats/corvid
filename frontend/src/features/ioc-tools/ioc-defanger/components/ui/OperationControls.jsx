import Box from '@mui/material/Box';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import FangIcon from '@mui/icons-material/GppMaybe';
import DefangIcon from '@mui/icons-material/HealthAndSafety';

const OperationControls = ({ operation, onSetOperation }) => {
  const handleChange = (_event, newOperation) => {
    if (newOperation) onSetOperation(newOperation);
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <ToggleButtonGroup
        value={operation}
        exclusive
        onChange={handleChange}
        size="small"
      >
        <ToggleButton value="defang" sx={{ gap: 0.75, px: 2, textTransform: 'none' }}>
          <DefangIcon fontSize="small" />
          Defang (Make Safe)
        </ToggleButton>
        <ToggleButton value="fang" sx={{ gap: 0.75, px: 2, textTransform: 'none' }}>
          <FangIcon fontSize="small" />
          Fang (Restore Original)
        </ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
};

export default OperationControls;
