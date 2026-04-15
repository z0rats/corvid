import { useState } from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Typography from '@mui/material/Typography';

export default function DeleteCategoryDialog({ open, category, templateCount, onClose, onConfirm }) {
  const [action, setAction] = useState('move_to_default');

  const handleConfirm = () => {
    onConfirm(category?.id, action);
    setAction('move_to_default');
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Delete Group</DialogTitle>
      <DialogContent>
        <Typography sx={{ mb: 2 }}>
          Are you sure you want to delete the group <strong>{category?.name}</strong>?
          {templateCount > 0 && ` It contains ${templateCount} template${templateCount !== 1 ? 's' : ''}.`}
        </Typography>
        {templateCount > 0 && (
          <RadioGroup value={action} onChange={e => setAction(e.target.value)}>
            <FormControlLabel
              value="move_to_default"
              control={<Radio />}
              label="Move templates to Default group"
            />
            <FormControlLabel
              value="delete_templates"
              control={<Radio />}
              label="Delete all templates in this group"
            />
          </RadioGroup>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleConfirm} color="error" variant="contained">
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
}
