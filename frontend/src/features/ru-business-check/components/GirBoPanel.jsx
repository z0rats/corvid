import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';

import RawResponsePanel from './RawResponsePanel';

const GIR_BO_URL = 'https://bo.nalog.gov.ru/';

// ГИР БО's own unit is thousand rubles; shown as reported, never rescaled.
function money(value) {
  if (value == null) return '—';
  return new Intl.NumberFormat('ru-RU').format(value);
}

/**
 * Financial statements from ГИР БО (bo.nalog.gov.ru): the last filed years' key lines. An
 * organization absent from the register (bank, insurer, never published) is a normal,
 * explained state - not a failure and not a clean bill of health.
 */
export default function GirBoPanel({ data, raw, inn, sha256 }) {
  if (!data?.checked) return null;

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" gutterBottom>Бухгалтерская отчётность (ГИР БО)</Typography>

      {data.years.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          {data.note || 'Отчётность не найдена'}
        </Typography>
      )}

      {data.years.length > 0 && (
        <>
          {data.note && <Alert severity="warning" sx={{ mb: 1 }}>{data.note}</Alert>}
          <Typography variant="caption" color="text.secondary">Суммы в {data.unit}, как в источнике</Typography>
          <Table size="small" sx={{ mt: 0.5 }}>
            <TableHead>
              <TableRow>
                <TableCell>Год</TableCell>
                <TableCell align="right">Выручка</TableCell>
                <TableCell align="right">Чистая прибыль</TableCell>
                <TableCell align="right">Итог баланса</TableCell>
                <TableCell align="right">Капитал и резервы</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.years.map((y) => (
                <TableRow key={y.year}>
                  <TableCell>{y.year}</TableCell>
                  <TableCell align="right">{money(y.revenue)}</TableCell>
                  <TableCell align="right">{money(y.net_profit)}</TableCell>
                  <TableCell align="right">{money(y.assets)}</TableCell>
                  <TableCell align="right">{money(y.equity)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}

      <Box sx={{ mt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Проверить вручную:{' '}
          <Link href={GIR_BO_URL} target="_blank" rel="noopener noreferrer">bo.nalog.gov.ru</Link>
          {inn ? <> — поиск по ИНН {inn}</> : null}
        </Typography>
      </Box>
      <RawResponsePanel label="Сырые данные ГИР БО" raw={raw} sha256={sha256} />
    </Paper>
  );
}
