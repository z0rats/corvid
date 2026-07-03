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

import { lookupHistoryApi } from '../../services/api/lookupHistoryApi';
import { createLogger } from '../../../../../../core/utils/logger';

const logger = createLogger('SingleLookupHistory');

export default function HistoryList() {
  const { t } = useTranslation('iocTools');
  const navigate = useNavigate();
  const [searches, setSearches] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadSearches = useCallback(async () => {
    try {
      setLoading(true);
      const data = await lookupHistoryApi.listSearches();
      setSearches(data);
    } catch (err) {
      logger.error('Failed to load lookup history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSearches(); }, [loadSearches]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await lookupHistoryApi.deleteSearch(id);
      setSearches((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      logger.error('Failed to delete lookup search:', err);
    }
  };

  if (loading) return <LinearProgress />;

  if (searches.length === 0) {
    return <Typography color="text.secondary">{t('singleLookup.history.empty')}</Typography>;
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{t('singleLookup.history.headers.ioc')}</TableCell>
            <TableCell>{t('singleLookup.history.headers.iocType')}</TableCell>
            <TableCell>{t('singleLookup.history.headers.searched')}</TableCell>
            <TableCell align="right">{t('singleLookup.history.headers.actions')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {searches.map((search) => (
            <TableRow
              key={search.id}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate(`/ioc-tools/lookup/history/${search.id}`)}
            >
              <TableCell sx={{ wordBreak: 'break-all' }}>{search.ioc}</TableCell>
              <TableCell>
                <Chip size="small" label={search.ioc_type} variant="outlined" />
              </TableCell>
              <TableCell>{new Date(search.searched_at).toLocaleString()}</TableCell>
              <TableCell align="right">
                <IconButton size="small" onClick={() => navigate(`/ioc-tools/lookup/history/${search.id}`)}>
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
