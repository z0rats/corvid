import { useEffect, useState, useCallback, useRef } from 'react';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';

import { createLogger } from '../utils/logger';

const logger = createLogger('HistoryTable');

/**
 * Shared "history" list shell for scan-style features: load / loading / empty /
 * delete / row-click-to-view. Each feature supplies only its column definitions
 * and API calls - see username-search, email-search, git-recon, reddit-search
 * and ioc-tools/single-lookup for usage.
 */
export default function HistoryTable({
  columns,
  fetchRows,
  onDelete,
  onRowClick,
  getRowId = (row) => row.id,
  emptyText,
  actionsLabel,
}) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  // Callers typically pass inline arrow functions for fetchRows/onDelete, so a
  // fresh reference lands on every parent render. Refs let load-on-mount stay
  // mount-only (matching the per-feature `useCallback(loadX, [])` this replaces)
  // instead of re-fetching whenever the parent re-renders for unrelated reasons.
  const fetchRowsRef = useRef(fetchRows);
  fetchRowsRef.current = fetchRows;
  const onDeleteRef = useRef(onDelete);
  onDeleteRef.current = onDelete;

  const loadRows = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchRowsRef.current();
      setRows(data);
    } catch (err) {
      logger.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRows(); }, [loadRows]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await onDeleteRef.current(id);
      setRows((prev) => prev.filter((row) => getRowId(row) !== id));
    } catch (err) {
      logger.error('Failed to delete history row:', err);
    }
  };

  if (loading) return <LinearProgress />;

  if (rows.length === 0) {
    return <Typography color="text.secondary">{emptyText}</Typography>;
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            {columns.map((col) => (
              <TableCell key={col.key} align={col.align}>{col.header}</TableCell>
            ))}
            <TableCell align="right">{actionsLabel}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => {
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
                  <IconButton size="small" onClick={() => onRowClick(row)}>
                    <VisibilityIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" onClick={(e) => handleDelete(id, e)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
