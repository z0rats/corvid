import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import RemoveIcon from '@mui/icons-material/RemoveCircleOutlined';

import CommitTextField from '../../../core/components/ui/CommitTextField';
import { getRunPath } from '../../../core/utils/historyPaths';

const MONO = { fontFamily: '"JetBrains Mono", monospace', fontSize: '0.85rem', wordBreak: 'break-all' };

/** The runs in an investigation. A missing run (deleted from history) keeps its row as a
 * tombstone: target and note stay, the link goes away. */
export default function ItemsTable({ items, featureLabels, onNoteChange, onRemove }) {
  const { t } = useTranslation('investigations');

  if (items.length === 0) {
    return <Typography color="text.secondary">{t('items.empty')}</Typography>;
  }

  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('items.headers.feature')}</TableCell>
            <TableCell>{t('items.headers.target')}</TableCell>
            <TableCell>{t('items.headers.added')}</TableCell>
            <TableCell sx={{ minWidth: 220 }}>{t('items.headers.note')}</TableCell>
            <TableCell align="right">{t('items.headers.actions')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>{featureLabels[item.feature] ?? item.feature}</TableCell>
              <TableCell>
                {item.missing ? (
                  <>
                    <Typography component="span" sx={{ ...MONO, mr: 1 }} color="text.secondary">
                      {item.target}
                    </Typography>
                    <Tooltip title={t('items.missingTooltip')}>
                      <Chip size="small" color="warning" variant="outlined" label={t('items.missing')} />
                    </Tooltip>
                  </>
                ) : (
                  <Link component={RouterLink} to={getRunPath(item.feature, item.run_id) ?? '#'} sx={MONO}>
                    {item.target}
                  </Link>
                )}
              </TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>{new Date(item.added_at).toLocaleString()}</TableCell>
              <TableCell>
                <CommitTextField
                  fullWidth
                  size="small"
                  variant="standard"
                  placeholder={t('items.notePlaceholder')}
                  value={item.note ?? ''}
                  onCommit={(note) => onNoteChange(item, note || null)}
                  slotProps={{ htmlInput: { maxLength: 5000, 'aria-label': t('items.headers.note') } }}
                />
              </TableCell>
              <TableCell align="right">
                <IconButton size="small" aria-label={t('items.remove')} onClick={() => onRemove(item)}>
                  <RemoveIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
