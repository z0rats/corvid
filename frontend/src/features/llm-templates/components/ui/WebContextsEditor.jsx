import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';

import WebContextEditor from './WebContextEditor';

export default function WebContextsEditor({ contexts, onAdd, onUpdate, onDelete }) {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Web contexts allow you to fetch content from websites when the template is executed.
          The content will be automatically extracted and included in the prompt.
        </Typography>
        <Button startIcon={<AddIcon />} size="small" onClick={onAdd}>Add Website</Button>
      </Box>
      {contexts.length > 0 ? (
        contexts.map((c, i) => (
          <WebContextEditor
            key={c.id || i}
            ctx={c}
            onUpdate={updated => onUpdate(i, updated)}
            onDelete={() => onDelete(i)}
          />
        ))
      ) : (
        <Typography color="text.secondary">No web contexts defined.</Typography>
      )}
    </Box>
  );
}
