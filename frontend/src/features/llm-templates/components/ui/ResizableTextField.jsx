import TextField from '@mui/material/TextField';
import { styled } from '@mui/material/styles';

const ResizableTextField = styled(TextField)({
  '& textarea': {
    resize: 'vertical',
    minHeight: '60px',
    fontSize: '0.9rem',
  },
  '& .MuiInputBase-root': {
    borderRadius: '8px',
  },
});

export default ResizableTextField;
