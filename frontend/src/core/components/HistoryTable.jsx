import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import InputAdornment from '@mui/material/InputAdornment';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import TextField from '@mui/material/TextField';
import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/SearchOutlined';
import VisibilityIcon from '@mui/icons-material/Visibility';

import ConfirmDeleteDialog from './ui/ConfirmDeleteDialog';
import PageHeader from './ui/PageHeader';
import { createLogger } from '../utils/logger';

const logger = createLogger('HistoryTable');

// Matches the backend list endpoints' default page (`LimitQuery`, max 500).
export const HISTORY_PAGE_SIZE = 100;
const MAX_REFRESH_LIMIT = 500;
export const RUNNING_REFRESH_MS = 5000;

const cellValue = (col, row) => (col.sortValue ? col.sortValue(row) : row[col.key]);

function compareValues(a, b) {
  if (a === b) return 0;
  if (a === null || a === undefined || a === '') return 1;
  if (b === null || b === undefined || b === '') return -1;
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
}

/**
 * Shared "history" list shell for scan-style features: load / loading / empty /
 * delete / row-click-to-view, plus paging ("Load more" via `fetchRows(skip, limit)`),
 * a text filter and column sorting over the loaded rows, and auto-refresh while any
 * loaded run is still `running`. Each feature supplies only its column definitions
 * and API calls - see username-search, email-search, git-recon, reddit-search
 * and ioc-tools/single-lookup for usage. A column's `sortValue(row)` overrides the
 * raw `row[key]` used for sorting/filtering (e.g. when `render` formats it). `title`, when
 * given, renders the page's PageHeader above it.
 */
export default function HistoryTable({ title, ...props }) {
  // Wraps the body rather than living in it: the body has several early returns (loading, empty,
  // error), and the page title must show in all of them.
  return (
    <>
      {title && <PageHeader title={title} />}
      <HistoryTableBody {...props} />
    </>
  );
}

function HistoryTableBody({
  columns,
  fetchRows,
  onDelete,
  onRowClick,
  getRowId = (row) => row.id,
  emptyText,
  actionsLabel,
}) {
  const { t } = useTranslation();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('');
  const [sort, setSort] = useState({ key: null, direction: 'asc' });
  // Row id awaiting delete confirmation - deleting drops the run's saved results for good.
  const [pendingDeleteId, setPendingDeleteId] = useState(null);

  // Callers typically pass inline arrow functions for fetchRows/onDelete, so a
  // fresh reference lands on every parent render. Refs let load-on-mount stay
  // mount-only (matching the per-feature `useCallback(loadX, [])` this replaces)
  // instead of re-fetching whenever the parent re-renders for unrelated reasons.
  const fetchRowsRef = useRef(fetchRows);
  fetchRowsRef.current = fetchRows;
  const onDeleteRef = useRef(onDelete);
  onDeleteRef.current = onDelete;
  const rowsRef = useRef(rows);
  rowsRef.current = rows;

  const loadRows = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchRowsRef.current(0, HISTORY_PAGE_SIZE);
      setRows(data);
      setHasMore(data.length >= HISTORY_PAGE_SIZE);
    } catch (err) {
      logger.error('Failed to load history:', err);
      setError(t('historyTable.loadFailed'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { loadRows(); }, [loadRows]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const data = await fetchRowsRef.current(rowsRef.current.length, HISTORY_PAGE_SIZE);
      setRows((prev) => {
        const seen = new Set(prev.map(getRowId));
        return [...prev, ...data.filter((row) => !seen.has(getRowId(row)))];
      });
      setHasMore(data.length >= HISTORY_PAGE_SIZE);
    } catch (err) {
      logger.error('Failed to load more history:', err);
      setError(t('historyTable.loadFailed'));
    } finally {
      setLoadingMore(false);
    }
  };

  // A run still in progress (started here or elsewhere) updates in place until it finishes.
  const hasRunning = rows.some((row) => row.status === 'running');
  useEffect(() => {
    if (!hasRunning) return undefined;
    const id = setInterval(async () => {
      try {
        const limit = Math.min(MAX_REFRESH_LIMIT, Math.max(HISTORY_PAGE_SIZE, rowsRef.current.length));
        setRows(await fetchRowsRef.current(0, limit));
      } catch (err) {
        logger.warn('Failed to refresh running history rows:', err);
      }
    }, RUNNING_REFRESH_MS);
    return () => clearInterval(id);
  }, [hasRunning]);

  const visibleRows = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    const filtered = needle
      ? rows.filter((row) => columns.some((col) => {
        const value = cellValue(col, row);
        return value !== null && value !== undefined && String(value).toLowerCase().includes(needle);
      }))
      : rows;
    if (!sort.key) return filtered;
    const col = columns.find((c) => c.key === sort.key);
    const sign = sort.direction === 'asc' ? 1 : -1;
    return [...filtered].sort((a, b) => sign * compareValues(cellValue(col, a), cellValue(col, b)));
  }, [rows, columns, filter, sort]);

  const toggleSort = (key) => setSort((prev) => (
    prev.key === key
      ? (prev.direction === 'asc' ? { key, direction: 'desc' } : { key: null, direction: 'asc' })
      : { key, direction: 'asc' }
  ));

  const requestDelete = (id, e) => {
    e.stopPropagation();
    setPendingDeleteId(id);
  };

  const confirmDelete = async () => {
    const id = pendingDeleteId;
    setPendingDeleteId(null);
    try {
      await onDeleteRef.current(id);
      setRows((prev) => prev.filter((row) => getRowId(row) !== id));
    } catch (err) {
      logger.error('Failed to delete history row:', err);
      setError(t('historyTable.deleteFailed'));
    }
  };

  if (loading) return <LinearProgress />;

  const errorAlert = error && (
    <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>{error}</Alert>
  );

  if (rows.length === 0) {
    return errorAlert || <Typography color="text.secondary">{emptyText}</Typography>;
  }

  return (
    <>
      {errorAlert}
      <TextField
        size="small"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder={t('historyTable.filterPlaceholder')}
        sx={{ mb: 2, width: { xs: '100%', sm: 320 } }}
        slotProps={{
          input: { startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> },
          htmlInput: { 'aria-label': t('historyTable.filterPlaceholder') },
        }}
      />
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.key} align={col.align} sortDirection={sort.key === col.key ? sort.direction : false}>
                  <TableSortLabel
                    active={sort.key === col.key}
                    direction={sort.key === col.key ? sort.direction : 'asc'}
                    onClick={() => toggleSort(col.key)}
                  >
                    {col.header}
                  </TableSortLabel>
                </TableCell>
              ))}
              <TableCell align="right">{actionsLabel}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleRows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length + 1}>
                  <Typography variant="body2" color="text.secondary">{t('historyTable.noMatches')}</Typography>
                </TableCell>
              </TableRow>
            )}
            {visibleRows.map((row) => {
              const id = getRowId(row);
              return (
                <TableRow
                  key={id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => onRowClick(row)}
                >
                  {columns.map((col) => (
                    <TableCell key={col.key} align={col.align} sx={col.cellSx}>
                      {col.render ? col.render(row) : row[col.key]}
                    </TableCell>
                  ))}
                  <TableCell align="right">
                    <Tooltip title={t('actions.view')}>
                      <IconButton size="small" onClick={(e) => { e.stopPropagation(); onRowClick(row); }} aria-label={t('actions.view')}>
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('actions.delete')}>
                      <IconButton size="small" onClick={(e) => requestDelete(id, e)} aria-label={t('actions.delete')}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
      {hasMore && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button onClick={loadMore} disabled={loadingMore}>
            {t('historyTable.loadMore')}
          </Button>
        </Box>
      )}
      <ConfirmDeleteDialog
        open={pendingDeleteId !== null}
        onClose={() => setPendingDeleteId(null)}
        onConfirm={confirmDelete}
        title={t('historyTable.confirmDeleteTitle')}
        message={t('historyTable.confirmDeleteMessage')}
      />
    </>
  );
}
