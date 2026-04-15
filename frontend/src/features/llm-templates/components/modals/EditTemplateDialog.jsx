import { useState, useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import ListSubheader from '@mui/material/ListSubheader';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Typography from '@mui/material/Typography';
import ConfirmDeleteDialog from '../../../../core/components/ui/ConfirmDeleteDialog';
import { MDXEditor, headingsPlugin, listsPlugin, quotePlugin, thematicBreakPlugin, markdownShortcutPlugin, codeBlockPlugin, codeMirrorPlugin, toolbarPlugin, BoldItalicUnderlineToggles, StrikeThroughSupSubToggles, ListsToggle, BlockTypeSelect, InsertThematicBreak, InsertCodeBlock } from '@mdxeditor/editor';
import '@mdxeditor/editor/style.css';

import { templatesApi } from '../../services/api/templatesApi';
import { apiKeysState } from '../../../../core/state/atoms';
import { AVAILABLE_MODELS } from '../../constants/templateConstants';
import { createLogger } from '../../../../core/utils/logger';
import ResizableTextField from '../ui/ResizableTextField';
import PayloadFieldsEditor from '../ui/PayloadFieldsEditor';
import StaticContextsEditor from '../ui/StaticContextsEditor';
import WebContextsEditor from '../ui/WebContextsEditor';

const logger = createLogger('EditTemplateDialog');

function ensureIds(items) {
  return items.map(item => item.id ? item : { ...item, id: crypto.randomUUID() });
}

function normalizeTemplate(template) {
  return {
    ...template,
    payload_fields: ensureIds(Array.isArray(template.payload_fields) ? template.payload_fields : []),
    static_contexts: ensureIds(Array.isArray(template.static_contexts) ? template.static_contexts : []),
    web_contexts: ensureIds(Array.isArray(template.web_contexts) ? template.web_contexts : []),
  };
}

export default function EditTemplateDialog({ open, onClose, template, onSave, onDelete: onDeleteSuccess, categories = [] }) {
  const theme = useTheme();
  const apiKeys = useAtomValue(apiKeysState);
  const [tpl, setTpl] = useState(() => template ? normalizeTemplate(template) : null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const availableModels = useMemo(
    () => AVAILABLE_MODELS.filter(m => apiKeys[m.apiKey]),
    [apiKeys]
  );

  if (!tpl) return null;

  const updateField = (key, value) => setTpl(prev => ({ ...prev, [key]: value }));

  const updateListItem = (listKey) => (idx, updated) =>
    setTpl(prev => ({ ...prev, [listKey]: prev[listKey].map((item, i) => (i === idx ? updated : item)) }));

  const deleteListItem = (listKey) => (idx) =>
    setTpl(prev => ({ ...prev, [listKey]: prev[listKey].filter((_, i) => i !== idx) }));

  const addListItem = (listKey, defaultItem) => () =>
    setTpl(prev => ({ ...prev, [listKey]: [...prev[listKey], { ...defaultItem, id: crypto.randomUUID() }] }));

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await templatesApi.updateTemplate(tpl.id, tpl);
      onSave(updated);
      onClose();
    } catch (err) {
      logger.error('Failed to save template:', err);
      alert('Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteConfirm = async () => {
    setDeleting(true);
    setDeleteDialogOpen(false);
    try {
      await templatesApi.deleteTemplate(tpl.id);
      onDeleteSuccess(tpl.id);
      onClose();
    } catch (err) {
      logger.error('Failed to delete template:', err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Edit Template</DialogTitle>
      <DialogContent dividers>
        <Typography variant="subtitle1" gutterBottom>Basic Information</Typography>
        <ResizableTextField label="Title" fullWidth value={tpl.title} onChange={e => updateField('title', e.target.value)} required sx={{ mb: 2 }} />
        <FormControl sx={{ minWidth: 200, mb: 2 }}>
          <InputLabel>LLM Model</InputLabel>
          <Select value={tpl.model} label="LLM Model" onChange={e => updateField('model', e.target.value)}>
            {Object.entries(Object.groupBy(availableModels, m => m.provider)).flatMap(([provider, models]) => [
              <ListSubheader key={provider}>{provider}</ListSubheader>,
              ...models.map(m => <MenuItem key={m.id} value={m.id}>{m.name}</MenuItem>),
            ])}
          </Select>
        </FormControl>
        <ResizableTextField label="Description" fullWidth multiline minRows={2} value={tpl.description} onChange={e => updateField('description', e.target.value)} />
        {categories.length > 0 && (
          <FormControl sx={{ minWidth: 200, mt: 2 }}>
            <InputLabel>Group</InputLabel>
            <Select
              value={tpl.category_id || ''}
              label="Group"
              onChange={e => updateField('category_id', e.target.value)}
            >
              {categories.map(c => (
                <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        <Box my={2}>
          <Typography variant="subtitle1" gutterBottom>AI Agent Configuration</Typography>
          <ResizableTextField label="AI Agent Role" fullWidth multiline minRows={1} value={tpl.ai_agent_role} onChange={e => updateField('ai_agent_role', e.target.value)} sx={{ mb: 2 }} />
          <ResizableTextField label="AI Agent Task" fullWidth multiline minRows={2} value={tpl.ai_agent_task} onChange={e => updateField('ai_agent_task', e.target.value)} />
        </Box>

        <Box my={2}>
          <PayloadFieldsEditor
            fields={tpl.payload_fields}
            onAdd={addListItem('payload_fields', { name: '', description: '', required: false })}
            onUpdate={updateListItem('payload_fields')}
            onDelete={deleteListItem('payload_fields')}
          />
        </Box>

        <Box my={2}>
          <StaticContextsEditor
            contexts={tpl.static_contexts}
            onAdd={addListItem('static_contexts', { name: '', description: '', content: '' })}
            onUpdate={updateListItem('static_contexts')}
            onDelete={deleteListItem('static_contexts')}
          />
        </Box>

        <Box my={2}>
          <WebContextsEditor
            contexts={tpl.web_contexts}
            onAdd={addListItem('web_contexts', { name: '', description: '', url: '' })}
            onUpdate={updateListItem('web_contexts')}
            onDelete={deleteListItem('web_contexts')}
          />
        </Box>

        <Box my={2}>
          <Typography variant="subtitle1" gutterBottom>Example (Markdown)</Typography>
          <Box className="mdxeditor-wrapper" sx={{ height: 300, minHeight: 100, resize: 'vertical', overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1.5 }}>
            <MDXEditor
              className={theme.palette.mode === 'dark' ? 'dark-theme' : ''}
              markdown={tpl.example_input_output || ''}
              onChange={val => updateField('example_input_output', val)}
              plugins={[
                headingsPlugin(),
                listsPlugin(),
                quotePlugin(),
                thematicBreakPlugin(),
                markdownShortcutPlugin(),
                codeBlockPlugin(),
                codeMirrorPlugin({ codeBlockLanguages: { '': 'Plain Text', js: 'JavaScript', python: 'Python', css: 'CSS', html: 'HTML', json: 'JSON', bash: 'Bash', text: 'Plain Text' } }),
                toolbarPlugin({ toolbarContents: () => (<><BlockTypeSelect /><BoldItalicUnderlineToggles /><StrikeThroughSupSubToggles /><ListsToggle /><InsertCodeBlock /><InsertThematicBreak /></>) }),
              ]}
            />
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button color="error" onClick={() => setDeleteDialogOpen(true)} disabled={deleting}>
          {deleting ? <CircularProgress size={20} /> : 'Delete'}
        </Button>
        <Box sx={{ flex: 1 }} />
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave} disabled={saving}>
          {saving ? <CircularProgress size={20} /> : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>

    <ConfirmDeleteDialog
      open={deleteDialogOpen}
      onClose={() => setDeleteDialogOpen(false)}
      onConfirm={handleDeleteConfirm}
      title="Delete Template"
      message="Are you sure you want to delete this template? This action cannot be undone."
    />
    </>
  );
}
