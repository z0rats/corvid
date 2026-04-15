import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';

import PayloadFieldEditor from './PayloadFieldEditor';

export default function PayloadFieldsEditor({ fields, onAdd, onUpdate, onDelete }) {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="body2">
          Payload fields are fields the user pastes / enters the data to that will be processed by the template.
        </Typography>
        <Button startIcon={<AddIcon />} size="small" onClick={onAdd}>Add Field</Button>
      </Box>
      {fields.length > 0 ? (
        fields.map((f, i) => (
          <PayloadFieldEditor
            key={f.id || i}
            field={f}
            onUpdate={updated => onUpdate(i, updated)}
            onDelete={() => onDelete(i)}
          />
        ))
      ) : (
        <Typography color="text.secondary">No payload fields defined.</Typography>
      )}
    </Box>
  );
}
