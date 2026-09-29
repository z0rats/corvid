import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

const MATCHED_ON_COLOR = {
  exact_name: 'success',
  exact_alias: 'success',
  substring_name: 'default',
  substring_alias: 'default',
};

export default function ResultsTable({ result }) {
  const { t } = useTranslation('sanctionsSearch');

  if (!result) return null;

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ mb: 1, alignItems: 'center' }}>
        <Typography variant="subtitle2">
          {t('results.summary', { count: result.total_matches })}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t('results.asOf', { date: result.as_of })}
        </Typography>
        {result.outdated && (
          <Chip size="small" color="warning" label={t('results.outdated')} />
        )}
      </Stack>

      {result.truncated && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t('results.truncated', { shown: result.matches.length, total: result.total_matches })}
        </Alert>
      )}

      {result.matches.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {t('results.empty')}
        </Typography>
      ) : (
        <TableContainer component={Paper} sx={{ boxShadow: 0, borderRadius: 1 }}>
          <Table aria-label="sanctions_results_table">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold' }}>{t('results.columns.name')}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{t('results.columns.schema')}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{t('results.columns.countries')}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{t('results.columns.programs')}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{t('results.columns.sanctions')}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{t('results.columns.lastSeen')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.matches.map((match) => (
                <TableRow key={match.opensanctions_id}>
                  <TableCell>
                    <Typography variant="body2">{match.name}</Typography>
                    {match.aliases.length > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        {match.aliases.join(', ')}
                      </Typography>
                    )}
                    <Box sx={{ mt: 0.5 }}>
                      <Chip
                        size="small"
                        color={MATCHED_ON_COLOR[match.matched_on] ?? 'default'}
                        label={t(`results.matchedOn.${match.matched_on}`)}
                      />
                    </Box>
                  </TableCell>
                  <TableCell>{match.schema}</TableCell>
                  <TableCell>{match.countries.join(', ')}</TableCell>
                  <TableCell>{match.programs.join(', ')}</TableCell>
                  <TableCell sx={{ maxWidth: 280 }}>
                    {match.sanctions ? (
                      <Tooltip title={match.sanctions}>
                        <Typography variant="body2" noWrap>
                          {match.sanctions}
                        </Typography>
                      </Tooltip>
                    ) : null}
                  </TableCell>
                  <TableCell>{match.last_seen}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
