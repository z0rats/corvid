import Box from '@mui/material/Box';
import Grow from '@mui/material/Grow';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import { useTheme } from '@mui/material/styles';
import { useServiceFilter } from '../../../shared/hooks/useServiceFilter';
import NoApiKeysAlert from './NoApiKeysAlert';
import ServiceFetcherRow from './ServiceFetcherRow';

function ResultTable({ ioc, iocType, filteredServices: externallyFilteredServices }) {
  const theme = useTheme();
  const servicesToRender = useServiceFilter(iocType, externallyFilteredServices);
  const headerBgColor = theme.palette.mode === 'dark' ? theme.palette.background.paper : 'inherit';

  if (servicesToRender.length === 0) {
    return <NoApiKeysAlert />;
  }

  return (
    <Grow in={true}>
      <Box>
        
        <TableContainer component={Paper} sx={{ boxShadow: 0, borderRadius: 1 }}>
          <Table aria-label="result_table">
            <TableHead>
              <TableRow sx={{ backgroundColor: `${headerBgColor} !important` }}>
                <TableCell sx={{ width: '5%' }} />
                <TableCell sx={{ fontWeight: "bold", width: '25%' }}>
                  Service
                </TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>
                  Result
                </TableCell>
                <TableCell sx={{ width: '5%' }} />
              </TableRow>
            </TableHead>
            <TableBody>
              {servicesToRender.map((serviceDefinition) => (
                <ServiceFetcherRow
                  key={serviceDefinition.key}
                  ioc={ioc}
                  iocType={iocType}
                  serviceConfigEntry={serviceDefinition}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Grow>
  );
}

export default ResultTable;
