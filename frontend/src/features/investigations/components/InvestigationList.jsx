import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';

import PageHeader from '../../../core/components/ui/PageHeader';
import ConfirmDeleteDialog from '../../../core/components/ui/ConfirmDeleteDialog';
import { investigationsService } from '../../../core/services/api/investigationsService';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('InvestigationList');

export default function InvestigationList() {
  const { t } = useTranslation('investigations');
  const { t: tCommon } = useTranslation();
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [name, setName] = useState('');
  const [pendingDelete, setPendingDelete] = useState(null);

  const load = useCallback(async () => {
    try {
      setRows(await investigationsService.list());
      setError(null);
    } catch (err) {
      logger.error('Failed to load investigations:', err);
      setError(t('list.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { load(); }, [load]);

  const create = async () => {
    const trimmed = name.trim();
    if (!trimmed) return;
    try {
      const created = await investigationsService.create(trimmed);
      navigate(`/investigations/${created.id}`);
    } catch (err) {
      logger.error('Failed to create investigation:', err);
      setError(t('list.createFailed'));
    }
  };

  const confirmDelete = async () => {
    const target = pendingDelete;
    setPendingDelete(null);
    try {
      await investigationsService.remove(target.id);
      setRows((current) => current.filter((row) => row.id !== target.id));
    } catch (err) {
      logger.error('Failed to delete investigation:', err);
      setError(t('list.deleteFailed'));
    }
  };

  return (
    <>
      <PageHeader title={tCommon('nav.investigations')} description={t('page.description')} />
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            fullWidth
            size="small"
            label={t('list.nameLabel')}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') create(); }}
            slotProps={{ htmlInput: { maxLength: 200 } }}
          />
          <Button variant="contained" onClick={create} disabled={!name.trim()}>
            {t('list.createButton')}
          </Button>
        </Stack>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading && <LinearProgress />}

      {!loading && rows.length === 0 && (
        <Typography color="text.secondary">{t('list.empty')}</Typography>
      )}

      {rows.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('list.headers.name')}</TableCell>
                <TableCell align="right">{t('list.headers.items')}</TableCell>
                <TableCell>{t('list.headers.updated')}</TableCell>
                <TableCell align="right">{t('list.headers.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => (
                <TableRow
                  key={row.id}
                  hover
                  onClick={() => navigate(`/investigations/${row.id}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>{row.name}</TableCell>
                  <TableCell align="right">{row.item_count}</TableCell>
                  <TableCell>{new Date(row.updated_at).toLocaleString()}</TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      aria-label={tCommon('actions.delete')}
                      onClick={(e) => { e.stopPropagation(); setPendingDelete(row); }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <ConfirmDeleteDialog
        open={Boolean(pendingDelete)}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        title={t('list.confirmDeleteTitle')}
        message={t('list.confirmDeleteMessage')}
      />
    </>
  );
}
