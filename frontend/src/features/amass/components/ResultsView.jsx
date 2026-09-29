import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

export default function ResultsView({ result }) {
  const { t } = useTranslation('amass');
  const hosts = result?.hosts || [];

  if (hosts.length === 0) {
    return <Typography color="text.secondary">{t('results.empty')}</Typography>;
  }

  return (
    <Box>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>
        {t('results.hostsFound', { count: hosts.length })}
      </Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('results.headers.hostname')}</TableCell>
              <TableCell>{t('results.headers.ip')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {hosts.map((h) => (
              <TableRow key={h.hostname} hover>
                <TableCell>{h.hostname}</TableCell>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {h.ip || '-'}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
