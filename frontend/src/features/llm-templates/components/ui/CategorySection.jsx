import { useState } from 'react';
import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { Droppable, Draggable } from '@hello-pangea/dnd';

import TemplateCard from './TemplateCard';

export default function CategorySection({
  category,
  templates,
  expanded,
  onToggle,
  selectedId,
  onSelect,
  onShowExample,
  onEdit,
  onDelete,
  onRenameCategory,
  onDeleteCategory,
  dragHandleProps,
}) {
  const [menuAnchor, setMenuAnchor] = useState(null);

  const handleMenuOpen = (e) => {
    e.stopPropagation();
    setMenuAnchor(e.currentTarget);
  };

  const handleMenuClose = () => setMenuAnchor(null);

  const handleRename = () => {
    handleMenuClose();
    onRenameCategory(category);
  };

  const handleDelete = () => {
    handleMenuClose();
    onDeleteCategory(category);
  };

  return (
    <Box sx={{ mb: 0.5 }}>
      <Box
        onClick={() => onToggle(category.id)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          cursor: 'pointer',
          py: 0.5,
          px: 1,
          borderRadius: 1,
          '&:hover': { bgcolor: 'action.hover' },
        }}
      >
        {!category.is_system && (
          <Box {...dragHandleProps} sx={{ display: 'flex', alignItems: 'center', cursor: 'grab', mr: 0.25 }}>
            <DragIndicatorIcon fontSize="small" sx={{ color: 'text.disabled' }} />
          </Box>
        )}
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 0.5 }}>
          {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
        </Box>
        <Typography variant="subtitle2" sx={{ flex: 1, fontWeight: 600 }}>
          {category.name}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
          {templates.length}
        </Typography>
        {!category.is_system && (
          <Tooltip title="Group options" arrow>
            <IconButton size="small" onClick={handleMenuOpen} sx={{ ml: 0.5 }}>
              <MoreVertIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {!category.is_system && (
        <Menu anchorEl={menuAnchor} open={Boolean(menuAnchor)} onClose={handleMenuClose}>
          <MenuItem onClick={handleRename}>
            <ListItemIcon><EditIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Rename</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleDelete}>
            <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon>
            <ListItemText sx={{ color: 'error.main' }}>Delete</ListItemText>
          </MenuItem>
        </Menu>
      )}

      <Collapse in={expanded}>
        <Droppable droppableId={category.id} type="template">
          {(provided) => (
            <Box
              ref={provided.innerRef}
              {...provided.droppableProps}
              sx={{ pt: 1, minHeight: expanded ? 8 : 0 }}
            >
              {templates.map((tpl, idx) => (
                <Draggable key={tpl.id} draggableId={tpl.id} index={idx}>
                  {(prov) => (
                    <Box
                      ref={prov.innerRef}
                      {...prov.draggableProps}
                      {...prov.dragHandleProps}
                      sx={{ mb: 0.5, cursor: 'grab' }}
                    >
                      <TemplateCard
                        template={tpl}
                        selected={selectedId === tpl.id}
                        onSelect={onSelect}
                        onShowExample={onShowExample}
                        onEdit={onEdit}
                        onDelete={onDelete}
                      />
                    </Box>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </Box>
          )}
        </Droppable>
      </Collapse>
    </Box>
  );
}
