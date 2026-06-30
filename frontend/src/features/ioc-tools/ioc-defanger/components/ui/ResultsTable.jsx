import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import Switch from '@mui/material/Switch';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import CopyIcon from '@mui/icons-material/ContentCopy';
import InfoIcon from '@mui/icons-material/Info';
import { useTranslation } from 'react-i18next';
import { getTypeColor } from '../../utils/defangerUtils';

const monospaceCellSx = { fontFamily: 'monospace', wordBreak: 'break-all' };
const typeChipsContainerSx = { display: 'flex', flexWrap: 'wrap', gap: 0.5 };

const ResultsTable = ({
  results,
  operation,
  showOnlyChanged,
  onToggleShowOnlyChanged,
  onCopy,
}) => {
  const { t } = useTranslation('iocTools');
  const filteredResults = showOnlyChanged ? results.filter((r) => r.changed) : results;
  const changedCount = results.filter((r) => r.changed).length;

  const noChangesMessages = {
    defang: t('iocDefanger.resultsTable.noChanges.defang'),
    fang: t('iocDefanger.resultsTable.noChanges.fang'),
  };

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {t('iocDefanger.resultsTable.title', { filteredCount: filteredResults.length, totalCount: results.length })}
        </Typography>
        <FormControlLabel
          control={
            <Switch
              checked={showOnlyChanged}
              onChange={(e) => onToggleShowOnlyChanged(e.target.checked)}
              sx={{ mr: 1 }}
            />
          }
          label={t('iocDefanger.resultsTable.showOnlyChanged', { count: changedCount })}
        />
      </Box>

      {changedCount === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon />
            {noChangesMessages[operation]}
          </Box>
        </Alert>
      )}

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('iocDefanger.resultsTable.columns.original')}</TableCell>
              <TableCell>{operation === 'defang' ? t('iocDefanger.resultsTable.columns.defanged') : t('iocDefanger.resultsTable.columns.fanged')}</TableCell>
              <TableCell>{t('iocDefanger.resultsTable.columns.types')}</TableCell>
              <TableCell>{t('iocDefanger.resultsTable.columns.status')}</TableCell>
              <TableCell align="center">{t('iocDefanger.resultsTable.columns.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredResults.map((result, index) => (
              <TableRow
                key={`${result.original}-${index}`}
                sx={{
                  backgroundColor: result.changed ? 'action.hover' : 'inherit',
                  '&:hover': { backgroundColor: 'action.selected' },
                }}
              >
                <TableCell>
                  <Typography variant="body2" sx={monospaceCellSx}>
                    {result.original}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{
                      fontFamily: 'monospace',
                      wordBreak: 'break-all',
                      fontWeight: result.changed ? 'bold' : 'normal',
                      color: result.changed ? 'primary.main' : 'inherit',
                    }}
                  >
                    {result.processed}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box sx={typeChipsContainerSx}>
                    {result.types.map((type) => (
                      <Chip
                        key={type}
                        label={type}
                        size="small"
                        color={getTypeColor(type)}
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={result.changed ? t('iocDefanger.resultsTable.status.modified') : t('iocDefanger.resultsTable.status.unchanged')}
                    size="small"
                    color={result.changed ? 'success' : 'default'}
                    variant={result.changed ? 'filled' : 'outlined'}
                  />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title={t('iocDefanger.resultsTable.copyResultTooltip')}>
                    <IconButton size="small" onClick={() => onCopy(result.processed, 'Result')} aria-label={t('iocDefanger.resultsTable.copyResultTooltip')}>
                      <CopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
};

export default ResultsTable;
