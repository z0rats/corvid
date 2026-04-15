import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';

export default function TemplateCard({ template, selected, onSelect, onShowExample, onEdit, onDelete }) {
  return (
    <Card
      variant="outlined"
      sx={{
        mb: 1,
        width: '100%',
        boxSizing: 'border-box',
        borderColor: selected ? 'primary.main' : 'transparent',
        borderWidth: selected ? 2 : 1,
        cursor: 'pointer',
        borderRadius: 2,
        boxShadow: 'none',
      }}
      onClick={() => onSelect(template)}
    >
      <Box display="flex">
        <CardContent sx={{ py: 1.5, px: 1.5, flex: 1, minWidth: 0 }}>
          <Typography variant="subtitle1" sx={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
            {template.title}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mt: 0.5,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {template.description}
          </Typography>
        </CardContent>
        <Stack
          justifyContent="center"
          spacing={0}
          sx={{
            pr: 0.5,
            py: 0.5,
            borderLeft: 1,
            borderColor: 'divider',
            pl: 0.5,
          }}
        >
          <IconButton size="small" onClick={e => { e.stopPropagation(); onShowExample(template); }} aria-label="View example">
            <Tooltip title="View Example" arrow><VisibilityIcon fontSize="small" /></Tooltip>
          </IconButton>
          <IconButton size="small" onClick={e => { e.stopPropagation(); onEdit(template); }} aria-label="Edit template">
            <Tooltip title="Edit Template" arrow><EditIcon fontSize="small" /></Tooltip>
          </IconButton>
          <IconButton size="small" onClick={e => { e.stopPropagation(); onDelete(template); }} aria-label="Delete template">
            <Tooltip title="Delete Template" arrow><DeleteIcon fontSize="small" /></Tooltip>
          </IconButton>
        </Stack>
      </Box>
    </Card>
  );
}
