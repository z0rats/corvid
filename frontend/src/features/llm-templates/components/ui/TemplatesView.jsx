import { useState, useCallback, useMemo } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import AppSnackbar from '../../../../core/components/ui/AppSnackbar';
import ConfirmDeleteDialog from '../../../../core/components/ui/ConfirmDeleteDialog';
import { styled } from '@mui/material/styles';
import { extractErrorMessage } from '../../../../core/utils/errorUtils';
import { useTemplates } from '../../hooks/api/useTemplates';
import { useCategories } from '../../hooks/api/useCategories';
import { useTemplateExecution } from '../../hooks/api/useTemplateExecution';
import { useTemplateSearch } from '../../hooks/ui/useTemplateSearch';
import { useCategoryCollapse } from '../../hooks/ui/useCategoryCollapse';
import { useNotification } from '../../../../core/hooks/ui/useNotification';
import { useDialogState } from '../../../../core/hooks/ui/useDialogState';
import { SYSTEM_CATEGORY_IDS } from '../../constants/templateConstants';
import TemplateSidebar from './TemplateSidebar';
import TemplateDetailPanel from './TemplateDetailPanel';
import LoadingSkeleton from './LoadingSkeleton';
import TemplateExampleDialog from '../modals/TemplateExampleDialog';
import EditTemplateDialog from '../modals/EditTemplateDialog';
import DeleteCategoryDialog from '../modals/DeleteCategoryDialog';
import RenameCategoryDialog from '../modals/RenameCategoryDialog';
import AddCategoryDialog from '../modals/AddCategoryDialog';

const MainContent = styled(Box)({
  flex: 1,
  overflowY: 'auto',
});

export default function TemplatesView() {
  const { templates, setTemplates, loading, error, fetchTemplates, reorderTemplates, deleteTemplate } = useTemplates();
  const {
    categories, createCategory, updateCategory, deleteCategory: deleteCategoryApi,
    reorderCategories, moveTemplates, fetchCategories,
  } = useCategories();
  const { executing, result, executeTemplate, clearResult } = useTemplateExecution();
  const { search, setSearch, isSearching } = useTemplateSearch(templates);
  const { isCategoryExpanded, toggleCategory } = useCategoryCollapse();
  const { notification: snackbar, showNotification: showSnackbar, hideNotification: closeSnackbar } = useNotification();

  const [selected, setSelected] = useState(null);
  const [payload, setPayload] = useState({});
  const exampleDialog = useDialogState();
  const editDialog = useDialogState();
  const deleteDialog = useDialogState();
  const renameCategoryDialog = useDialogState();
  const deleteCategoryDialog = useDialogState();
  const [addCategoryOpen, setAddCategoryOpen] = useState(false);

  const handleSelect = useCallback((tpl) => {
    setSelected(tpl);
    setPayload({});
    clearResult();
  }, [clearResult]);

  const handlePayloadChange = useCallback((name, value) => {
    setPayload(prev => ({ ...prev, [name]: value }));
  }, []);

  const handleExecute = useCallback(async () => {
    if (!selected) return;
    try {
      await executeTemplate(selected, payload);
      showSnackbar('Template executed successfully!', 'success');
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    }
  }, [selected, payload, executeTemplate, showSnackbar]);

  // --- Drag-end handler: supports both category and template drags ---
  const handleDragEnd = useCallback(async (dragResult) => {
    if (!dragResult.destination) return;
    const { type, source, destination } = dragResult;

    try {
      if (type === 'category') {
        // Prevent dropping into system category positions
        const systemCount = categories.filter(c => c.is_system).length;
        if (destination.index < systemCount) return;
        await reorderCategories(source.index, destination.index);
      } else if (type === 'template') {
        const sourceCatId = source.droppableId;
        const destCatId = destination.droppableId;

        if (sourceCatId === destCatId) {
          // Reorder within same category
          const catTemplates = templates
            .filter(t => t.category_id === sourceCatId)
            .sort((a, b) => (a.order_number || 0) - (b.order_number || 0));

          const [moved] = catTemplates.splice(source.index, 1);
          catTemplates.splice(destination.index, 0, moved);

          // Update local state
          const reorderedIds = new Set(catTemplates.map(t => t.id));
          const otherTemplates = templates.filter(t => !reorderedIds.has(t.id));
          setTemplates([...otherTemplates, ...catTemplates]);

          await reorderTemplates(
            templates.findIndex(t => t.id === moved.id),
            destination.index,
          );
        } else {
          // Move between categories
          const movedTemplateId = dragResult.draggableId;
          await moveTemplates([movedTemplateId], destCatId);
          setTemplates(prev =>
            prev.map(t => t.id === movedTemplateId ? { ...t, category_id: destCatId } : t)
          );
        }
      }
    } catch {
      showSnackbar('Failed to update order', 'error');
      fetchTemplates();
      fetchCategories();
    }
  }, [templates, setTemplates, categories, reorderTemplates, reorderCategories, moveTemplates, fetchTemplates, fetchCategories, showSnackbar]);

  // --- Template CRUD handlers ---
  const handleDelete = useCallback((tpl) => {
    deleteDialog.openDialog(tpl);
  }, [deleteDialog]);

  const handleDeleteConfirm = useCallback(async () => {
    const tplToDelete = deleteDialog.item;
    deleteDialog.closeDialog();
    try {
      await deleteTemplate(tplToDelete.id);
      if (selected?.id === tplToDelete.id) setSelected(null);
      showSnackbar('Template deleted successfully!', 'success');
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    }
  }, [deleteTemplate, deleteDialog, selected, showSnackbar]);

  const handleCopyResult = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(result);
      showSnackbar('Result copied to clipboard!', 'success');
    } catch {
      showSnackbar('Failed to copy to clipboard', 'error');
    }
  }, [result, showSnackbar]);

  const openExample = useCallback((tpl) => { exampleDialog.openDialog(tpl); }, [exampleDialog]);
  const openEdit = useCallback((tpl) => { editDialog.openDialog(tpl); }, [editDialog]);

  const handleEditSave = useCallback((updated) => {
    setTemplates(prev => prev.map(t => t.id === updated.id ? updated : t));
    if (selected?.id === updated.id) setSelected(updated);
    showSnackbar('Template updated successfully!', 'success');
  }, [setTemplates, selected, showSnackbar]);

  const handleEditDelete = useCallback((deletedId) => {
    setTemplates(prev => prev.filter(t => t.id !== deletedId));
    if (selected?.id === deletedId) setSelected(null);
    showSnackbar('Template deleted successfully!', 'success');
  }, [setTemplates, selected, showSnackbar]);

  const handleToggleFavorite = useCallback(async (tpl) => {
    const isFavorite = tpl.category_id === SYSTEM_CATEGORY_IDS.FAVORITES;
    const newCategoryId = isFavorite ? SYSTEM_CATEGORY_IDS.DEFAULT : SYSTEM_CATEGORY_IDS.FAVORITES;
    try {
      await moveTemplates([tpl.id], newCategoryId);
      setTemplates(prev =>
        prev.map(t => t.id === tpl.id ? { ...t, category_id: newCategoryId } : t)
      );
      if (selected?.id === tpl.id) {
        setSelected(prev => ({ ...prev, category_id: newCategoryId }));
      }
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    }
  }, [moveTemplates, setTemplates, selected, showSnackbar]);

  // --- Category CRUD handlers ---
  const handleAddCategory = useCallback(async (name) => {
    setAddCategoryOpen(false);
    try {
      await createCategory(name);
      showSnackbar('Group created!', 'success');
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    }
  }, [createCategory, showSnackbar]);

  const handleRenameCategory = useCallback(async (categoryId, newName) => {
    renameCategoryDialog.closeDialog();
    try {
      await updateCategory(categoryId, newName);
      showSnackbar('Group renamed!', 'success');
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    }
  }, [updateCategory, renameCategoryDialog, showSnackbar]);

  const deleteCategoryTemplateCount = useMemo(() => {
    if (!deleteCategoryDialog.item) return 0;
    return templates.filter(t => t.category_id === deleteCategoryDialog.item.id).length;
  }, [deleteCategoryDialog.item, templates]);

  const handleDeleteCategory = useCallback(async (categoryId, action) => {
    deleteCategoryDialog.closeDialog();
    try {
      await deleteCategoryApi(categoryId, action);
      if (action === 'delete_templates') {
        setTemplates(prev => prev.filter(t => t.category_id !== categoryId));
      } else {
        setTemplates(prev =>
          prev.map(t => t.category_id === categoryId ? { ...t, category_id: SYSTEM_CATEGORY_IDS.DEFAULT } : t)
        );
      }
      showSnackbar('Group deleted!', 'success');
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    }
  }, [deleteCategoryApi, deleteCategoryDialog, setTemplates, showSnackbar]);

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
          <Button size="small" onClick={fetchTemplates} sx={{ ml: 2 }}>Retry</Button>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 0, m: 0 }}>
      {loading ? (
        <LoadingSkeleton />
      ) : templates.length === 0 && categories.length === 0 ? (
        <Alert severity="info" sx={{ mb: 2 }}>No templates available</Alert>
      ) : (
        <Box display="flex" sx={{ height: 'calc(100vh - 120px)' }}>
          <TemplateSidebar
            templates={templates}
            categories={categories}
            totalCount={templates.length}
            search={search}
            isSearching={isSearching}
            onSearchChange={setSearch}
            selectedId={selected?.id}
            onSelect={handleSelect}
            onShowExample={openExample}
            onEdit={openEdit}
            onDelete={handleDelete}
            onDragEnd={handleDragEnd}
            isCategoryExpanded={isCategoryExpanded}
            onToggleCategory={toggleCategory}
            onRenameCategory={(cat) => renameCategoryDialog.openDialog(cat)}
            onDeleteCategory={(cat) => deleteCategoryDialog.openDialog(cat)}
            onAddCategory={() => setAddCategoryOpen(true)}
          />
          <MainContent>
            <TemplateDetailPanel
              template={selected}
              payload={payload}
              onPayloadChange={handlePayloadChange}
              executing={executing}
              result={result}
              onExecute={handleExecute}
              onCopyResult={handleCopyResult}
              onShowExample={openExample}
              onEdit={openEdit}
              onToggleFavorite={handleToggleFavorite}
              search={search}
              onClearSearch={() => setSearch('')}
            />
          </MainContent>
        </Box>
      )}

      <TemplateExampleDialog open={exampleDialog.open} template={exampleDialog.item} onClose={exampleDialog.closeDialog} />

      {editDialog.item && (
        <EditTemplateDialog
          key={editDialog.item?.id || 'new'}
          open={editDialog.open}
          template={editDialog.item}
          categories={categories}
          onSave={handleEditSave}
          onDelete={handleEditDelete}
          onClose={editDialog.closeDialog}
        />
      )}

      <AppSnackbar open={snackbar.open} message={snackbar.message} severity={snackbar.severity} onClose={closeSnackbar} />

      <ConfirmDeleteDialog
        open={deleteDialog.open}
        onClose={deleteDialog.closeDialog}
        onConfirm={handleDeleteConfirm}
        title="Delete Template"
        message="Are you sure you want to delete this template? This action cannot be undone."
      />

      <AddCategoryDialog
        open={addCategoryOpen}
        onClose={() => setAddCategoryOpen(false)}
        onConfirm={handleAddCategory}
      />

      <RenameCategoryDialog
        open={renameCategoryDialog.open}
        category={renameCategoryDialog.item}
        onClose={renameCategoryDialog.closeDialog}
        onConfirm={handleRenameCategory}
      />

      <DeleteCategoryDialog
        open={deleteCategoryDialog.open}
        category={deleteCategoryDialog.item}
        templateCount={deleteCategoryTemplateCount}
        onClose={deleteCategoryDialog.closeDialog}
        onConfirm={handleDeleteCategory}
      />
    </Box>
  );
}
