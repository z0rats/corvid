import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';

export default function ResultsTable({ result }) {
  const { t } = useTranslation('dorkRunner');

  if (!result) return null;

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t('results.summary', { count: result.total_results, queries: result.queries_run })}
      </Typography>

      {result.errors && result.errors.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t('results.someQueriesFailed', { count: result.errors.length })}
        </Alert>
      )}

      {result.results.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {t('results.empty')}
        </Typography>
      ) : (
        <TableContainer component={Paper} sx={{ boxShadow: 0, borderRadius: 1 }}>
          <Table aria-label="dork_results_table">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', width: '15%' }}>{t('results.columns.template')}</TableCell>
                <TableCell sx={{ fontWeight: 'bold', width: '35%' }}>{t('results.columns.title')}</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>{t('results.columns.snippet')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.results.map((item, index) => (
                <TableRow key={`${item.template_key}-${index}`}>
                  <TableCell>
                    <Chip label={item.template_key} size="small" />
                  </TableCell>
                  <TableCell>
                    <Link href={item.url} target="_blank" rel="noopener noreferrer">
                      {item.title || item.url}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {item.snippet}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
