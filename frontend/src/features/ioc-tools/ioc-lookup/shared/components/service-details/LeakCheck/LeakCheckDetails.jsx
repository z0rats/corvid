import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import NoDetails from '../NoDetails';

// "YYYY-MM" sorts lexically; an undated source ("") goes last.
const byDateDesc = (a, b) => (b.date || '').localeCompare(a.date || '');

export default function LeakCheckDetails({ result }) {
  const { t } = useTranslation('iocTools');

  if (!result) {
    return <NoDetails message={t('providers.leakcheck.unavailable')} />;
  }

  const { sources = [], fields = [] } = result;

  if (sources.length === 0) {
    return (
      <Card sx={{ p: 2, m: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircleIcon color="success" />
          <Typography variant="h6">{t('providers.leakcheck.notFound')}</Typography>
        </Box>
      </Card>
    );
  }

  return (
    <Card sx={{ p: 2, m: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <WarningAmberIcon color="warning" />
        <Typography variant="h6">{t('providers.leakcheck.foundIn', { count: sources.length })}</Typography>
      </Box>

      {fields.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('providers.leakcheck.exposedFields')}</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
            {fields.map((field) => (
              <Chip key={field} label={field} size="small" variant="outlined" />
            ))}
          </Box>
        </Box>
      )}

      <Table size="small" aria-label={t('providers.leakcheck.sourcesTable')}>
        <TableHead>
          <TableRow>
            <TableCell>{t('providers.leakcheck.source')}</TableCell>
            <TableCell>{t('providers.leakcheck.date')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {/* name + date isn't unique (several undated "Stealer Logs"), so the index joins the key */}
          {[...sources].sort(byDateDesc).map((source, index) => (
            <TableRow key={`${index}-${source.name}-${source.date}`}>
              <TableCell>{source.name}</TableCell>
              <TableCell>{source.date || t('providers.leakcheck.unknownDate')}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        {t('providers.leakcheck.disclaimer')}
      </Typography>
    </Card>
  );
}
