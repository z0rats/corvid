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
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';

import { gitReconApi } from '../services/api/gitReconApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('GitReconHistory');
const STATUS_COLORS = { running: 'info', completed: 'success', failed: 'error' };

export default function HistoryList() {
  const { t } = useTranslation('gitRecon');
  const navigate = useNavigate();
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadSearches = useCallback(async () => {
    try {
      setLoading(true);
      const data = await gitReconApi.listHistory();
      setSearches(data);
    } catch (err) {
      logger.error('Failed to load search history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSearches(); }, [loadSearches]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await gitReconApi.deleteHistory(id);
      setSearches((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      logger.error('Failed to delete search:', err);
    }
  };

  if (loading) return <LinearProgress />;

  if (searches.length === 0) {
    return <Typography color="text.secondary">{t('history.empty')}</Typography>;
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{t('history.headers.mode')}</TableCell>
            <TableCell>{t('history.headers.target')}</TableCell>
            <TableCell>{t('history.headers.status')}</TableCell>
            <TableCell>{t('history.headers.persons')}</TableCell>
            <TableCell>{t('history.headers.repos')}</TableCell>
            <TableCell>{t('history.headers.searched')}</TableCell>
            <TableCell align="right">{t('history.headers.actions')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {searches.map((search) => (
            <TableRow
              key={search.id}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate(`/git-recon/history/${search.id}`)}
            >
              <TableCell><Chip size="small" label={t(`form.modes.${search.mode}`)} /></TableCell>
              <TableCell>{search.target}</TableCell>
              <TableCell>
                <Chip size="small" label={t(`history.status.${search.status}`)} color={STATUS_COLORS[search.status] || 'default'} />
              </TableCell>
              <TableCell>{search.persons_found}</TableCell>
              <TableCell>{search.mode === 'search' ? '-' : `${search.repos_scanned}/${search.repos_scanned + search.repos_failed}`}</TableCell>
              <TableCell>{new Date(search.searched_at).toLocaleString()}</TableCell>
              <TableCell align="right">
                <IconButton size="small" onClick={() => navigate(`/git-recon/history/${search.id}`)}>
                  <VisibilityIcon fontSize="small" />
                </IconButton>
                <IconButton size="small" onClick={(e) => handleDelete(search.id, e)}>
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
