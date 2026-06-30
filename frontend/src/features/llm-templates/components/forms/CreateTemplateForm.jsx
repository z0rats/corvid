import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation('llmTemplates');
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
      showSnackbar(t('createForm.promptEngineeredSuccess'), 'success');
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
      showSnackbar(t('createForm.templateCreatedSuccess'), 'success');
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
        title={t('createForm.basicInfo')}
        actions={
          <Tooltip title={t('createForm.engineerTooltip')} arrow>
            <IconButton onClick={handleEngineer} disabled={!canEngineer} aria-label={t('createForm.optimizePromptAria')}>
              {isEngineering ? <CircularProgress size={24} /> : <AutoFixHighIcon />}
            </IconButton>
          </Tooltip>
        }
      >
        <Box display="flex" gap={2} alignItems="flex-start">
          <ResizableTextField
            label={t('createForm.titleLabel')}
            value={template.title}
            onChange={e => updateField('title', e.target.value)}
            fullWidth required
            error={!template.title.trim()}
            helperText={!template.title.trim() ? t('createForm.titleRequiredHelper') : t('createForm.titleHelper')}
            sx={{ flex: 1 }}
          />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>{t('createForm.modelLabel')}</InputLabel>
            <Select value={template.model} label={t('createForm.modelLabel')} onChange={e => updateField('model', e.target.value)}>
              {Object.entries(Object.groupBy(availableModels, m => m.provider)).flatMap(([provider, models]) => [
                <ListSubheader key={provider}>{provider}</ListSubheader>,
                ...models.map(m => <MenuItem key={m.id} value={m.id}>{m.name}</MenuItem>),
              ])}
            </Select>
          </FormControl>
          {categories.length > 0 && (
            <FormControl sx={{ minWidth: 180 }}>
              <InputLabel>{t('createForm.groupLabel')}</InputLabel>
              <Select
                value={template.category_id || ''}
                label={t('createForm.groupLabel')}
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
            label={t('createForm.descriptionLabel')}
            value={template.description}
            onChange={e => updateField('description', e.target.value)}
            fullWidth multiline minRows={2}
            helperText={t('createForm.descriptionHelper')}
          />
        </Box>
      </FormSection>

      <FormSection title={t('createForm.promptConfig')}>
        <ResizableTextField
          label={t('createForm.agentRoleLabel')}
          value={template.ai_agent_role}
          onChange={e => updateField('ai_agent_role', e.target.value)}
          fullWidth multiline minRows={1} required
          error={!template.ai_agent_role.trim()}
          helperText={!template.ai_agent_role.trim() ? t('createForm.agentRoleRequiredHelper') : t('createForm.agentRoleHelper')}
        />
        <Box mt={2}>
          <ResizableTextField
            label={t('createForm.agentTaskLabel')}
            value={template.ai_agent_task}
            onChange={e => updateField('ai_agent_task', e.target.value)}
            fullWidth multiline minRows={2} required
            error={!template.ai_agent_task.trim()}
            helperText={!template.ai_agent_task.trim() ? t('createForm.agentTaskRequiredHelper') : t('createForm.agentTaskHelper')}
          />
        </Box>
      </FormSection>

      <FormSection title={t('createForm.payloadFieldsSection')}>
        <PayloadFieldsEditor
          fields={template.payload_fields}
          onAdd={payloadFields.add}
          onUpdate={payloadFields.update}
          onDelete={payloadFields.delete}
        />
        <FormHelperText sx={{ mt: 1 }}>{t('createForm.payloadFieldsHelper')}</FormHelperText>
      </FormSection>

      <FormSection title={t('createForm.staticContextsSection')}>
        <StaticContextsEditor
          contexts={template.static_contexts}
          onAdd={staticContexts.add}
          onUpdate={staticContexts.update}
          onDelete={staticContexts.delete}
        />
        <FormHelperText sx={{ mt: 1 }}>{t('createForm.staticContextsHelper')}</FormHelperText>
      </FormSection>

      <FormSection title={t('createForm.webContextsSection')}>
        <WebContextsEditor
          contexts={template.web_contexts}
          onAdd={webContexts.add}
          onUpdate={webContexts.update}
          onDelete={webContexts.delete}
        />
        <FormHelperText sx={{ mt: 1 }}>{t('createForm.webContextsHelper')}</FormHelperText>
      </FormSection>

      <FormSection title={t('createForm.previewExampleSection')}>
        <FormHelperText sx={{ mt: -1, mb: 1 }}>{t('createForm.previewExampleTopHelper')}</FormHelperText>
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
        <FormHelperText sx={{ mt: 1 }}>{t('createForm.previewExampleBottomHelper')}</FormHelperText>
      </FormSection>

      <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
        <Button startIcon={<PreviewIcon />} onClick={() => setPreviewOpen(true)}>{t('createForm.previewButton')}</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!isValid || isSubmitting}
          startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
          sx={{ ml: 2 }}
        >
          {isSubmitting ? t('createForm.creatingButton') : t('createForm.createButton')}
        </Button>
      </Box>

      <TemplateExampleDialog open={previewOpen} template={template} onClose={() => setPreviewOpen(false)} />

      <AppSnackbar open={snackbar.open} message={snackbar.message} severity={snackbar.severity} onClose={closeSnackbar} />
    </Box>
  );
}
