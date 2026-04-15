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
import { getTypeColor } from '../../utils/defangerUtils';

const monospaceCellSx = { fontFamily: 'monospace', wordBreak: 'break-all' };
const typeChipsContainerSx = { display: 'flex', flexWrap: 'wrap', gap: 0.5 };

const NO_CHANGES_MESSAGES = {
  defang: 'No IOCs were modified. They may already be defanged or not recognized as IOCs.',
  fang: 'No IOCs were modified. They may already be fanged or not contain defanged patterns.',
};

const ResultsTable = ({
  results,
  operation,
  showOnlyChanged,
  onToggleShowOnlyChanged,
  onCopy,
}) => {
  const filteredResults = showOnlyChanged ? results.filter((r) => r.changed) : results;
  const changedCount = results.filter((r) => r.changed).length;

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Results ({filteredResults.length} of {results.length} IOCs)
        </Typography>
        <FormControlLabel
          control={
            <Switch
              checked={showOnlyChanged}
              onChange={(e) => onToggleShowOnlyChanged(e.target.checked)}
              sx={{ mr: 1 }}
            />
          }
          label={`Show only changed (${changedCount})`}
        />
      </Box>

      {changedCount === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon />
            {NO_CHANGES_MESSAGES[operation]}
          </Box>
        </Alert>
      )}

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Original</TableCell>
              <TableCell>{operation === 'defang' ? 'Defanged' : 'Fanged'}</TableCell>
              <TableCell>Type(s)</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center">Actions</TableCell>
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
                    label={result.changed ? 'Modified' : 'Unchanged'}
                    size="small"
                    color={result.changed ? 'success' : 'default'}
                    variant={result.changed ? 'filled' : 'outlined'}
                  />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Copy result">
                    <IconButton size="small" onClick={() => onCopy(result.processed, 'Result')} aria-label="Copy result">
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
