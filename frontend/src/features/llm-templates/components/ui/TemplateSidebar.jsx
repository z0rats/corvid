import { useMemo } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';

import TemplateCard from './TemplateCard';
import CategorySection from './CategorySection';

const SidebarContainer = styled(Box)(({ theme }) => ({
  flex: '0 0 400px',
  overflowY: 'auto',
  paddingRight: theme.spacing(1),
  '&::-webkit-scrollbar': { width: 6 },
  '&::-webkit-scrollbar-track': { background: 'transparent' },
  '&::-webkit-scrollbar-thumb': {
    background: theme.palette.action.disabled,
    borderRadius: 3,
  },
  '&::-webkit-scrollbar-thumb:hover': {
    background: theme.palette.action.active,
  },
  scrollbarWidth: 'thin',
  scrollbarColor: `${theme.palette.action.disabled} transparent`,
}));

export default function TemplateSidebar({
  templates,
  categories,
  totalCount,
  search,
  isSearching,
  onSearchChange,
  selectedId,
  onSelect,
  onShowExample,
  onEdit,
  onDelete,
  onDragEnd,
  isCategoryExpanded,
  onToggleCategory,
  onRenameCategory,
  onDeleteCategory,
  onAddCategory,
}) {
  const templatesByCategory = useMemo(() => {
    const grouped = {};
    for (const cat of categories) {
      grouped[cat.id] = [];
    }
    for (const tpl of templates) {
      const catId = tpl.category_id;
      if (grouped[catId]) {
        grouped[catId].push(tpl);
      } else if (categories.length > 0) {
        // Fallback: put in first available category
        const fallbackId = categories[categories.length - 1].id;
        if (grouped[fallbackId]) {
          grouped[fallbackId].push(tpl);
        }
      }
    }
    return grouped;
  }, [templates, categories]);

  const searchResults = useMemo(() => {
    if (!isSearching) return [];
    const term = search.toLowerCase().trim();
    return templates.filter(t =>
      t.title.toLowerCase().includes(term) ||
      (t.description && t.description.toLowerCase().includes(term))
    );
  }, [templates, search, isSearching]);

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <SidebarContainer>
        <TextField
          size="small"
          fullWidth
          placeholder={`Search templates (${totalCount})...`}
          value={search}
          onChange={e => onSearchChange(e.target.value)}
          slotProps={{
            input: {
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              sx: { borderRadius: 1 },
            },
          }}
          sx={{ mb: 1 }}
        />

        {isSearching ? (
          <>
            {searchResults.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                No templates match your search
              </Typography>
            ) : (
              <Droppable droppableId="search-results" type="template" isDropDisabled>
                {(provided) => (
                  <Box ref={provided.innerRef} {...provided.droppableProps}>
                    {searchResults.map((tpl, idx) => (
                      <Draggable key={tpl.id} draggableId={tpl.id} index={idx} isDragDisabled>
                        {(prov) => (
                          <Box ref={prov.innerRef} {...prov.draggableProps} {...prov.dragHandleProps} sx={{ mb: 0.5 }}>
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
            )}
          </>
        ) : (
          <Droppable droppableId="category-list" type="category">
            {(provided) => (
              <Box ref={provided.innerRef} {...provided.droppableProps}>
                {categories.map((cat, idx) => (
                  <Draggable key={cat.id} draggableId={`cat-${cat.id}`} index={idx} isDragDisabled={cat.is_system}>
                    {(prov) => (
                      <Box ref={prov.innerRef} {...prov.draggableProps}>
                        <CategorySection
                          category={cat}
                          templates={templatesByCategory[cat.id] || []}
                          expanded={isCategoryExpanded(cat.id)}
                          onToggle={onToggleCategory}
                          selectedId={selectedId}
                          onSelect={onSelect}
                          onShowExample={onShowExample}
                          onEdit={onEdit}
                          onDelete={onDelete}
                          onRenameCategory={onRenameCategory}
                          onDeleteCategory={onDeleteCategory}
                          dragHandleProps={prov.dragHandleProps}
                        />
                      </Box>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </Box>
            )}
          </Droppable>
        )}

        {!isSearching && (
          <Box
            onClick={onAddCategory}
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              py: 0.5,
              px: 1,
              borderRadius: 1,
              mt: 0.5,
              '&:hover': { bgcolor: 'action.hover' },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
              <AddIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
              <Typography variant="subtitle2" color="text.secondary">
                Add Group
              </Typography>
            </Box>
          </Box>
        )}
      </SidebarContainer>
    </DragDropContext>
  );
}
