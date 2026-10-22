import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';

import ApiDownloadButtons from '../../../core/components/ui/ApiDownloadButtons';
import CommitTextField from '../../../core/components/ui/CommitTextField';
import ConfirmDeleteDialog from '../../../core/components/ui/ConfirmDeleteDialog';
import { investigationsService } from '../../../core/services/api/investigationsService';
import { createLogger } from '../../../core/utils/logger';
import { useFeatureLabels } from '../hooks/useFeatureLabels';
import EntityGraph from './EntityGraph';
import ItemsTable from './ItemsTable';

const logger = createLogger('InvestigationDetail');

const REPORT_FORMATS = ['html', 'pdf'];

export default function InvestigationDetail() {
  const { t, i18n } = useTranslation('investigations');
  const { t: tCommon } = useTranslation();
  const { id } = useParams();
  const navigate = useNavigate();
  const featureLabels = useFeatureLabels();
  const [investigation, setInvestigation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notesDraft, setNotesDraft] = useState('');
  const [tab, setTab] = useState('items');
  const [confirmDelete, setConfirmDelete] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await investigationsService.get(id);
      setInvestigation(data);
      setNotesDraft(data.notes ?? '');
    } catch (err) {
      logger.error('Failed to load investigation:', err);
      setInvestigation(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const save = async (fields) => {
    try {
      const data = await investigationsService.update(id, fields);
      setInvestigation(data);
      setError(null);
    } catch (err) {
      logger.error('Failed to update investigation:', err);
      setError(t('detail.saveFailed'));
    }
  };

  const updateNote = async (item, note) => {
    try {
      const updated = await investigationsService.updateItem(id, item.id, note);
      setInvestigation((current) => ({
        ...current,
        items: current.items.map((row) => (row.id === item.id ? updated : row)),
      }));
    } catch (err) {
      logger.error('Failed to update item note:', err);
      setError(t('detail.saveFailed'));
    }
  };

  const removeItem = async (item) => {
    try {
      await investigationsService.removeItem(id, item.id);
      setInvestigation((current) => ({
        ...current,
        items: current.items.filter((row) => row.id !== item.id),
      }));
    } catch (err) {
      logger.error('Failed to remove item:', err);
      setError(t('items.removeFailed'));
    }
  };

  const remove = async () => {
    setConfirmDelete(false);
    try {
      await investigationsService.remove(id);
      navigate('/investigations');
    } catch (err) {
      logger.error('Failed to delete investigation:', err);
      setError(t('detail.saveFailed'));
    }
  };

  const locale = i18n.language?.startsWith('ru') ? 'ru' : 'en';

  if (loading) return <LinearProgress />;
  if (!investigation) return <Typography color="text.secondary">{t('detail.notFound')}</Typography>;

  const notesDirty = notesDraft !== (investigation.notes ?? '');

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, flexWrap: 'wrap' }}>
        <IconButton onClick={() => navigate('/investigations')} aria-label={tCommon('actions.back')}>
          <ArrowBackIcon />
        </IconButton>
        <CommitTextField
          size="small"
          label={t('detail.nameLabel')}
          value={investigation.name}
          onCommit={(name) => { if (name.trim()) save({ name: name.trim() }); }}
          slotProps={{ htmlInput: { maxLength: 200 } }}
          sx={{ minWidth: 260, flexGrow: { xs: 1, sm: 0 } }}
        />
        <Typography variant="body2" color="text.secondary">
          {t('detail.created', { date: new Date(investigation.created_at).toLocaleDateString() })}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, ml: 'auto', flexWrap: 'wrap' }}>
          {investigation.items.length > 0 && (
            <ApiDownloadButtons
              formats={REPORT_FORMATS}
              request={(format) => investigationsService.reportRequest(investigation.id, format, locale)}
            />
          )}
          <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => setConfirmDelete(true)}>
            {t('detail.deleteButton')}
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

      <Paper sx={{ p: 2, mb: 2 }}>
        <TextField
          fullWidth
          multiline
          minRows={2}
          maxRows={10}
          label={t('detail.notesLabel')}
          placeholder={t('detail.notesPlaceholder')}
          value={notesDraft}
          onChange={(e) => setNotesDraft(e.target.value)}
          slotProps={{ htmlInput: { maxLength: 20000 } }}
        />
        {notesDirty && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <Button size="small" variant="contained" onClick={() => save({ notes: notesDraft || null })}>
              {t('detail.saveNotes')}
            </Button>
          </Box>
        )}
      </Paper>

      <Tabs value={tab} onChange={(_e, value) => setTab(value)} sx={{ mb: 2 }}>
        <Tab value="items" label={t('detail.tabs.items', { count: investigation.items.length })} />
        <Tab value="graph" label={t('detail.tabs.graph')} />
      </Tabs>

      {tab === 'items' ? (
        <ItemsTable
          items={investigation.items}
          featureLabels={featureLabels}
          onNoteChange={updateNote}
          onRemove={removeItem}
        />
      ) : (
        <EntityGraph
          investigationId={investigation.id}
          investigationName={investigation.name}
          featureLabels={featureLabels}
          refreshKey={investigation.items.length}
        />
      )}

      <ConfirmDeleteDialog
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
        onConfirm={remove}
        title={t('list.confirmDeleteTitle')}
        message={t('list.confirmDeleteMessage')}
      />
    </Box>
  );
}
