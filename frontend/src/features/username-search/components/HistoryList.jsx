import { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';

import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchHistory');
const STATUS_COLORS = { running: 'info', completed: 'success', cancelled: 'warning', failed: 'error' };

export default function HistoryList() {
  const { t } = useTranslation('usernameSearch');
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadRuns = useCallback(async () => {
    try {
      setLoading(true);
      const data = await usernameSearchApi.listRuns();
      setRuns(data);
    } catch (err) {
      logger.error('Failed to load search history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRuns(); }, [loadRuns]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await usernameSearchApi.deleteRun(id);
      setRuns((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      logger.error('Failed to delete search run:', err);
    }
  };

  if (loading) return <LinearProgress />;

  if (runs.length === 0) {
    return <Typography color="text.secondary">{t('history.empty')}</Typography>;
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{t('history.headers.username')}</TableCell>
            <TableCell>{t('history.headers.source')}</TableCell>
            <TableCell>{t('history.headers.status')}</TableCell>
            <TableCell>{t('history.headers.found')}</TableCell>
            <TableCell>{t('history.headers.started')}</TableCell>
            <TableCell align="right">{t('history.headers.actions')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.map((run) => (
            <TableRow
              key={run.id}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate(`/username-search/history/${run.id}`)}
            >
              <TableCell>{run.username}</TableCell>
              <TableCell>
                <Chip size="small" variant="outlined" label={t(`form.source${run.source === 'social_analyzer' ? 'SocialAnalyzer' : 'Maigret'}`)} />
              </TableCell>
              <TableCell>
                <Chip size="small" label={t(`history.status.${run.status}`)} color={STATUS_COLORS[run.status] || 'default'} />
              </TableCell>
              <TableCell>{run.found_count}</TableCell>
              <TableCell>{new Date(run.started_at).toLocaleString()}</TableCell>
              <TableCell align="right">
                <IconButton size="small" onClick={() => navigate(`/username-search/history/${run.id}`)}>
                  <VisibilityIcon fontSize="small" />
                </IconButton>
                <IconButton size="small" onClick={(e) => handleDelete(run.id, e)}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
