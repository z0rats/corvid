import { useState, useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import ListSubheader from '@mui/material/ListSubheader';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Tooltip from '@mui/material/Tooltip';
import AppSnackbar from '../../../../core/components/ui/AppSnackbar';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import PreviewIcon from '@mui/icons-material/Preview';
import { MDXEditor, headingsPlugin, listsPlugin, quotePlugin, thematicBreakPlugin, markdownShortcutPlugin, codeBlockPlugin, codeMirrorPlugin, toolbarPlugin, BoldItalicUnderlineToggles, StrikeThroughSupSubToggles, ListsToggle, BlockTypeSelect, InsertThematicBreak, InsertCodeBlock } from '@mdxeditor/editor';
import '@mdxeditor/editor/style.css';

import { templatesApi } from '../../services/api/templatesApi';
import { extractErrorMessage } from '../../../../core/utils/errorUtils';
import { useTemplateForm } from '../../hooks/ui/useTemplateForm';
import { useCategories } from '../../hooks/api/useCategories';
import { useNotification } from '../../../../core/hooks/ui/useNotification';
import { isTemplateFormValid } from '../../utils/templateValidation';
import { apiKeysState } from '../../../../core/state/atoms';
import { AVAILABLE_MODELS } from '../../constants/templateConstants';
import FormSection from '../ui/FormSection';
import ResizableTextField from '../ui/ResizableTextField';
import PayloadFieldsEditor from '../ui/PayloadFieldsEditor';
import StaticContextsEditor from '../ui/StaticContextsEditor';
import WebContextsEditor from '../ui/WebContextsEditor';
import TemplateExampleDialog from '../modals/TemplateExampleDialog';

export default function CreateTemplateForm() {
  const {
    template, updateField, resetForm,
    payloadFields, staticContexts, webContexts,
  } = useTemplateForm();
  const theme = useTheme();
  const apiKeys = useAtomValue(apiKeysState);
  const { categories } = useCategories();
  const { notification: snackbar, showNotification: showSnackbar, hideNotification: closeSnackbar } = useNotification();
  const [previewOpen, setPreviewOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEngineering, setIsEngineering] = useState(false);

  const availableModels = useMemo(
    () => AVAILABLE_MODELS.filter(m => apiKeys[m.apiKey]),
    [apiKeys]
  );

  const canEngineer = useMemo(
    () => template.title.trim() && template.description.trim(),
    [template.title, template.description]
  );

  const isValid = useMemo(() => isTemplateFormValid(template), [template]);

  const handleEngineer = async () => {
    if (!canEngineer) return;
    setIsEngineering(true);
    try {
      const data = await templatesApi.engineerPrompt({
        title: template.title,
        description: template.description,
        model_id: template.model,
      });
      updateField('ai_agent_role', data.ai_agent_role);
      updateField('ai_agent_task', data.ai_agent_task);
      updateField('payload_fields', data.payload_fields);
      updateField('example_input_output', data.example_input_output);
      showSnackbar('Prompt engineered!', 'success');
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    } finally {
      setIsEngineering(false);
    }
  };

  const handleSubmit = async () => {
    if (!isValid) return;
    setIsSubmitting(true);
    try {
      await templatesApi.createTemplate(template);
      showSnackbar('Template created!', 'success');
      resetForm();
    } catch (err) {
      showSnackbar(extractErrorMessage(err), 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box sx={{ pt: 0 }}>
      <FormSection
        title="Basic Information"
        actions={
          <Tooltip title="Generate template based on title and description" arrow>
            <IconButton onClick={handleEngineer} disabled={!canEngineer} aria-label="Optimize prompt">
              {isEngineering ? <CircularProgress size={24} /> : <AutoFixHighIcon />}
            </IconButton>
          </Tooltip>
        }
      >
        <Box display="flex" gap={2} alignItems="flex-start">
          <ResizableTextField
            label="Title"
            value={template.title}
            onChange={e => updateField('title', e.target.value)}
            fullWidth required
            error={!template.title.trim()}
            helperText={!template.title.trim() ? 'Enter a concise template title (required)' : 'Unique name for your template.'}
            sx={{ flex: 1 }}
          />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>LLM Model</InputLabel>
            <Select value={template.model} label="LLM Model" onChange={e => updateField('model', e.target.value)}>
              {Object.entries(Object.groupBy(availableModels, m => m.provider)).flatMap(([provider, models]) => [
                <ListSubheader key={provider}>{provider}</ListSubheader>,
                ...models.map(m => <MenuItem key={m.id} value={m.id}>{m.name}</MenuItem>),
              ])}
            </Select>
          </FormControl>
          {categories.length > 0 && (
            <FormControl sx={{ minWidth: 180 }}>
              <InputLabel>Group</InputLabel>
              <Select
                value={template.category_id || ''}
                label="Group"
                onChange={e => updateField('category_id', e.target.value)}
              >
                {categories.map(c => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>
        <Box mt={2}>
          <ResizableTextField
            label="Description"
            value={template.description}
            onChange={e => updateField('description', e.target.value)}
            fullWidth multiline minRows={2}
            helperText="Summarize what this template is for (optional)."
          />
        </Box>
      </FormSection>

      <FormSection title="Prompt Configuration">
        <ResizableTextField
          label="AI Agent Role"
          value={template.ai_agent_role}
          onChange={e => updateField('ai_agent_role', e.target.value)}
          fullWidth multiline minRows={1} required
          error={!template.ai_agent_role.trim()}
          helperText={!template.ai_agent_role.trim() ? 'Define the AI persona (required)' : 'E.g., Customer support expert.'}
        />
        <Box mt={2}>
          <ResizableTextField
            label="AI Agent Task"
            value={template.ai_agent_task}
            onChange={e => updateField('ai_agent_task', e.target.value)}
            fullWidth multiline minRows={2} required
            error={!template.ai_agent_task.trim()}
            helperText={!template.ai_agent_task.trim() ? 'Describe the task (required)' : 'E.g., Generate a friendly response.'}
          />
        </Box>
      </FormSection>

      <FormSection title="Payload Fields">
        <PayloadFieldsEditor
          fields={template.payload_fields}
          onAdd={payloadFields.add}
          onUpdate={payloadFields.update}
          onDelete={payloadFields.delete}
        />
        <FormHelperText sx={{ mt: 1 }}>Set user-input variables and mark them as required if needed.</FormHelperText>
      </FormSection>

      <FormSection title="Static Contexts">
        <StaticContextsEditor
          contexts={template.static_contexts}
          onAdd={staticContexts.add}
          onUpdate={staticContexts.update}
          onDelete={staticContexts.delete}
        />
        <FormHelperText sx={{ mt: 1 }}>Include fixed content like guidelines or reference info.</FormHelperText>
      </FormSection>

      <FormSection title="Web Contexts">
        <WebContextsEditor
          contexts={template.web_contexts}
          onAdd={webContexts.add}
          onUpdate={webContexts.update}
          onDelete={webContexts.delete}
        />
        <FormHelperText sx={{ mt: 1 }}>Add websites whose content will be fetched and included when the template is executed.</FormHelperText>
      </FormSection>

      <FormSection title="Preview Example">
        <FormHelperText sx={{ mt: -1, mb: 1 }}>Provide an example to illustrate how input and output could look like when this template is used.</FormHelperText>
        <Box className="mdxeditor-wrapper" sx={{ height: 300, minHeight: 100, resize: 'vertical', overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1.5 }}>
          <MDXEditor
            className={theme.palette.mode === 'dark' ? 'dark-theme' : ''}
            markdown={template.example_input_output || ''}
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
        <FormHelperText sx={{ mt: 1 }}>Provide example input & output to guide users.</FormHelperText>
      </FormSection>

      <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
        <Button startIcon={<PreviewIcon />} onClick={() => setPreviewOpen(true)}>Preview</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!isValid || isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
          sx={{ ml: 2 }}
        >
          {isSubmitting ? 'Creating\u2026' : 'Create Template'}
        </Button>
      </Box>

      <TemplateExampleDialog open={previewOpen} template={template} onClose={() => setPreviewOpen(false)} />

      <AppSnackbar open={snackbar.open} message={snackbar.message} severity={snackbar.severity} onClose={closeSnackbar} />
    </Box>
  );
}
