import { useTranslation } from 'react-i18next';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import { useTheme } from '@mui/material/styles';
import ServiceResultRow from '../ui/ServiceResultRow';
import { SERVICE_DEFINITIONS } from '../../../shared/config/serviceConfig';

export default function HistoryResultTable({ ioc, iocType, results }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const headerBgColor = theme.palette.mode === 'dark' ? theme.palette.background.paper : 'inherit';

  return (
    <TableContainer component={Paper} sx={{ boxShadow: 0, borderRadius: 1 }}>
      <Table aria-label="history_result_table">
        <TableHead>
          <TableRow sx={{ backgroundColor: `${headerBgColor} !important` }}>
            <TableCell sx={{ width: '5%' }} />
            <TableCell sx={{ fontWeight: "bold", width: '25%' }}>
              {t('singleLookup.resultTable.columns.service')}
            </TableCell>
            <TableCell sx={{ fontWeight: "bold" }}>
              {t('singleLookup.resultTable.columns.result')}
            </TableCell>
            <TableCell sx={{ width: '5%' }} />
          </TableRow>
        </TableHead>
        <TableBody>
          {results.map((item) => {
            const frontendConfig = SERVICE_DEFINITIONS[item.service_key] || {};
            return (
              <ServiceResultRow
                key={item.service_key}
                serviceKey={item.service_key}
                service={{
                  name: item.service_name,
                  icon: frontendConfig.icon,
                  detailComponent: frontendConfig.detailComponent,
                }}
                loading={false}
                result={item.data}
                summary={item.summary}
                tlp={item.tlp}
                ioc={ioc}
                iocType={iocType}
              />
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
