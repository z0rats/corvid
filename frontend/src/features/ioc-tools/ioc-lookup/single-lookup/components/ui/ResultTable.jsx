import { useCallback, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
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

function ResultTable({ ioc, iocType, filteredServices: externallyFilteredServices, onSearchComplete, bypassCache = false }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const servicesToRender = useServiceFilter(iocType, externallyFilteredServices);
  const headerBgColor = theme.palette.mode === 'dark' ? theme.palette.background.paper : 'inherit';

  const resultsMapRef = useRef(new Map());
  const savedRef = useRef(false);

  useEffect(() => {
    resultsMapRef.current = new Map();
    savedRef.current = false;
  }, [ioc, iocType]);

  const handleServiceResult = useCallback((serviceKey, resultEntry) => {
    resultsMapRef.current.set(serviceKey, resultEntry);
    if (savedRef.current || !onSearchComplete) return;
    if (resultsMapRef.current.size < servicesToRender.length) return;

    savedRef.current = true;
    const entries = servicesToRender.map((service) => resultsMapRef.current.get(service.key));
    // Replaying a lookup entirely from this session's cache (e.g. Back from another tool) is
    // not a new search - don't write a duplicate history row for it.
    if (entries.every((entry) => entry.fromCache)) return;
    onSearchComplete({
      ioc,
      iocType,
      results: servicesToRender.map((service, index) => {
        const { fromCache: _fromCache, ...entry } = entries[index];
        return { service_key: service.key, ...entry };
      }),
    });
  }, [servicesToRender, ioc, iocType, onSearchComplete]);

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
                  {t('singleLookup.resultTable.columns.service')}
                </TableCell>
                <TableCell sx={{ fontWeight: "bold" }}>
                  {t('singleLookup.resultTable.columns.result')}
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
                  onResult={handleServiceResult}
                  bypassCache={bypassCache}
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
