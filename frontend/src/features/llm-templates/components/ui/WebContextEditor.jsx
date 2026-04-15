import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import DeleteIcon from '@mui/icons-material/Delete';
import LanguageIcon from '@mui/icons-material/Language';

import ResizableTextField from './ResizableTextField';

export default function WebContextEditor({ ctx, onUpdate, onDelete }) {
  return (
    <Paper sx={{ mb: 1.5, p: 1.5 }}>
      <Box display="flex" flexDirection="column" gap={1.5}>
        <Box display="flex" gap={2} alignItems="flex-start">
          <ResizableTextField
            label="Context Name"
            value={ctx.name}
            onChange={e => onUpdate({ ...ctx, name: e.target.value })}
            size="small"
            sx={{ flex: 1 }}
            required
            error={!ctx.name.trim()}
            helperText={!ctx.name.trim() ? 'Required' : ''}
          />
          <ResizableTextField
            label="Description"
            value={ctx.description}
            onChange={e => onUpdate({ ...ctx, description: e.target.value })}
            size="small"
            sx={{ flex: 2 }}
            placeholder="Optional description of what this website provides"
            helperText=""
          />
          <Box display="flex" alignItems="center">
            <IconButton color="error" onClick={onDelete} aria-label="Delete context">
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
        <ResizableTextField
          label="Website URL"
          value={ctx.url}
          onChange={e => onUpdate({ ...ctx, url: e.target.value })}
          fullWidth
          required
          error={!ctx.url.trim()}
          helperText={!ctx.url.trim() ? 'Required - Enter a valid HTTP/HTTPS URL' : 'The website content will be fetched when the template is executed'}
          placeholder="https://example.com/page"
          slotProps={{
            input: {
              startAdornment: <LanguageIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            },
          }}
        />
      </Box>
    </Paper>
  );
}
