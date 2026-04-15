import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';

import StaticContextEditor from './StaticContextEditor';

export default function StaticContextsEditor({ contexts, onAdd, onUpdate, onDelete }) {
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Static contexts allow you to add static data that will be included in the prompt.
        </Typography>
        <Button startIcon={<AddIcon />} size="small" onClick={onAdd}>Add Context</Button>
      </Box>
      {contexts.length > 0 ? (
        contexts.map((c, i) => (
          <StaticContextEditor
            key={c.id || i}
            ctx={c}
            onUpdate={updated => onUpdate(i, updated)}
            onDelete={() => onDelete(i)}
          />
        ))
      ) : (
        <Typography color="text.secondary">No static contexts defined.</Typography>
      )}
    </Box>
  );
}
