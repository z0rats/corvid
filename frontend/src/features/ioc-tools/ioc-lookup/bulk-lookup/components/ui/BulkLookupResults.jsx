import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import TablePagination from '@mui/material/TablePagination';
import Typography from '@mui/material/Typography';
import IocCard from './IocCard';
import WelcomeScreen from './WelcomeScreen';

const ROWS_PER_PAGE_OPTIONS = [10, 25, 50, 100];
const DEFAULT_ROWS_PER_PAGE = 10;

function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ioc-tabpanel-${index}`}
      aria-labelledby={`ioc-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index) {
  return {
    id: `ioc-tab-${index}`,
    'aria-controls': `ioc-tabpanel-${index}`,
  };
}

export default function BulkLookupResults({
  categorizedIocs,
  orderedIocTypes,
  activeTab,
  onTabChange,
  loading,
  progress,
  error,
}) {
  const { t } = useTranslation('iocTools');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(DEFAULT_ROWS_PER_PAGE);

  // Switching tabs shows a different IOC list, so the previous page number
  // no longer applies - reset back to the first page.
  useEffect(() => {
    setPage(0);
  }, [activeTab]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (error) {
    return <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>;
  }

  if (loading) {
    return (
      <Box sx={{ width: '100%', mb: 2 }}>
        <LinearProgress variant="determinate" value={progress} />
        <Typography variant="caption" sx={{ display: 'block' }} align="center">
          {t('bulkLookup.results.progress', { percent: Math.round(progress) })}
        </Typography>
      </Box>
    );
  }

  const hasResults = !loading && !error && orderedIocTypes.length > 0 && Object.values(categorizedIocs).some(arr => arr.length > 0);

  if (!hasResults) {
    return <WelcomeScreen />;
  }
  
  return (
    <Paper sx={{ mt: 2 }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={activeTab}
          onChange={onTabChange}
          aria-label={t('bulkLookup.results.tabsAriaLabel')}
          variant="scrollable"
          scrollButtons="auto"
        >
          {orderedIocTypes.map((typeKey, index) => (
            <Tab
              key={typeKey}
              label={`${typeKey.toUpperCase()} (${categorizedIocs[typeKey]?.length || 0})`}
              {...a11yProps(index)}
            />
          ))}
        </Tabs>
      </Box>
      {orderedIocTypes.map((typeKey, index) => {
        const iocs = categorizedIocs[typeKey] || [];
        const pagedIocs = index === activeTab
          ? iocs.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
          : [];

        return (
          <TabPanel value={activeTab} index={index} key={typeKey}>
            {iocs.length > 0 ? (
              <>
                {pagedIocs.map((ioc) => (
                  <IocCard key={ioc.id} ioc={ioc} />
                ))}
                {iocs.length > ROWS_PER_PAGE_OPTIONS[0] && (
                  <TablePagination
                    rowsPerPageOptions={ROWS_PER_PAGE_OPTIONS}
                    component="div"
                    count={iocs.length}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                  />
                )}
              </>
            ) : (
              <Typography>{t('bulkLookup.results.emptyTab', { type: typeKey.toUpperCase() })}</Typography>
            )}
          </TabPanel>
        );
      })}
    </Paper>
  );
}
