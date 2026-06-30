import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardMedia from '@mui/material/CardMedia';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Pagination from '@mui/material/Pagination';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import PublicIcon from '@mui/icons-material/Public';
import NumbersIcon from '@mui/icons-material/Numbers';
import LinkIcon from '@mui/icons-material/Link';
import HttpIcon from '@mui/icons-material/Http';
import TagIcon from '@mui/icons-material/Tag';

function NoDetails({ message }) {
  return (
    <Paper sx={{ p: 3, textAlign: 'center', margin: 1 }}>
      <Typography variant="h6">{message}</Typography>
    </Paper>
  );
}

function DetailItem({ label, value, defaultVal }) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return (
    <ListItem disableGutters dense>
      <ListItemText
        primary={
          <Typography variant="body2" component="span" fontWeight="bold">
            {label}:
          </Typography>
        }
        secondary={
          <Typography variant="body2" component="span" color="text.secondary" sx={{ ml: 1, wordBreak: 'break-all' }}>
            {value || defaultVal}
          </Typography>
        }
      />
    </ListItem>
  );
}


export default function UrlScanDetails({ result }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const [page, setPage] = useState(1);
  const rowsPerPage = 5;

  const scans = useMemo(() => result?.results || [], [result?.results]);

  const paginatedScans = useMemo(() => {
    return scans.slice(
      (page - 1) * rowsPerPage,
      page * rowsPerPage
    );
  }, [scans, page, rowsPerPage]);

  const uniqueDomains = useMemo(() => {
    const domains = new Set(scans.map(s => s.task.apexDomain).filter(Boolean));
    return domains.size;
  }, [scans]);

  const uniqueIPs = useMemo(() => {
    const ips = new Set(scans.map(s => s.page.ip).filter(Boolean));
    return ips.size;
  }, [scans]);

  if (!result || !scans.length) {
    return <NoDetails message={t('providers.urlscan.noInfoFound')} />;
  }

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const formatDate = (dateString) => {
    if (!dateString) return notAvailable;
    return new Date(dateString).toLocaleString();
  }

  return (
    <Box sx={{ margin: 1 }}>
      {/* Summary Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ p: 2, height: '100%' }}>
            <Box display="flex" alignItems="center">
              <NumbersIcon fontSize="large" sx={{ mr: 1, color: 'text.primary' }} />
              <Box>
                <Typography variant="h6">{t('providers.urlscan.totalScans')}</Typography>
                <Typography variant="h4">{result.total}</Typography>
              </Box>
            </Box>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ p: 2, height: '100%' }}>
            <Box display="flex" alignItems="center">
              <PublicIcon fontSize="large" sx={{ mr: 1, color: 'text.primary' }} />
              <Box>
                <Typography variant="h6">{t('providers.urlscan.uniqueApexDomains')}</Typography>
                <Typography variant="h4">{uniqueDomains}</Typography>
              </Box>
            </Box>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Card sx={{ p: 2, height: '100%' }}>
            <Box display="flex" alignItems="center">
              <HttpIcon fontSize="large" sx={{ mr: 1, color: 'text.primary' }} />
              <Box>
                <Typography variant="h6">{t('providers.urlscan.uniqueIps')}</Typography>
                <Typography variant="h4">{uniqueIPs}</Typography>
              </Box>
            </Box>
          </Card>
        </Grid>
      </Grid>

      {/* Accordion for Scan Results */}
      <Accordion defaultExpanded sx={{ "&::before": { display: "none" } }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box display="flex" alignItems="center">
            <TravelExploreIcon sx={{ mr: 1 }} />
            <Typography variant="h6">{t('providers.urlscan.scanResults', { count: scans.length })}</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {paginatedScans.map((scan) => (
            <Card key={scan._id} sx={{ display: 'flex', mb: 2, flexDirection: { xs: 'column', md: 'row' } }}>
                <CardMedia
                    component="img"
                    sx={{ width: { xs: '100%', md: 300 }, height: 225, objectFit: 'cover', borderRight: (t) => ({ md: `1px solid ${t.palette.divider}` }) }}
                    image={scan.screenshot}
                    alt={t('providers.urlscan.screenshotAlt', { url: scan.task.url })}
                    onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/300x225/EEE/31343C?text=No+Screenshot'; }}
                />
              <Grid container spacing={2} sx={{ p: 2 }}>
                <Grid size={{ xs: 12, md: 6 }}>
                   <Typography variant="h6" component="div" sx={{ wordBreak: 'break-all' }}>
                      {scan.task.domain || notAvailable}
                    </Typography>
                  <Link href={scan.result} target="_blank" rel="noopener noreferrer" sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                     <LinkIcon fontSize="small" sx={{ mr: 0.5 }} /> {t('providers.urlscan.viewFullReport')}
                  </Link>

                  <Box display="flex" flexWrap="wrap" gap={1} mb={1}>
                    {(scan.task.tags || []).map(tag => (
                        <Chip icon={<TagIcon />} key={tag} label={tag} size="small" color="secondary" />
                    ))}
                  </Box>

                  <List dense>
                     <DetailItem label={t('providers.urlscan.scanTime')} value={formatDate(scan.task.time)} defaultVal={notAvailable} />
                     <DetailItem label={t('providers.urlscan.scannedUrl')} value={scan.task.url} defaultVal={notAvailable} />
                     <DetailItem label={t('providers.urlscan.visibility')} value={scan.task.visibility} defaultVal={notAvailable} />
                  </List>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle1" fontWeight="bold">{t('providers.urlscan.pageDetails')}</Typography>
                  <List dense>
                    <DetailItem label={t('providers.urlscan.finalUrl')} value={scan.page.url} defaultVal={notAvailable} />
                    <DetailItem label={t('providers.urlscan.title')} value={scan.page.title} defaultVal={notAvailable} />
                    <DetailItem label={t('providers.urlscan.ipAddress')} value={scan.page.ip} defaultVal={notAvailable} />
                    <DetailItem label={t('providers.urlscan.country')} value={scan.page.country} defaultVal={notAvailable} />
                    <DetailItem label={t('providers.urlscan.asn')} value={`${scan.page.asn} (${scan.page.asnname})`} defaultVal={notAvailable} />
                    <DetailItem label={t('providers.urlscan.server')} value={scan.page.server} defaultVal={notAvailable} />
                    <DetailItem label={t('providers.urlscan.status')} value={scan.page.status} defaultVal={notAvailable} />
                    <DetailItem label={t('providers.urlscan.mimeType')} value={scan.page.mimeType} defaultVal={notAvailable} />
                  </List>
                </Grid>
              </Grid>
            </Card>
          ))}
          {scans.length > rowsPerPage && (
            <Box display="flex" justifyContent="center" mt={2}>
              <Pagination
                count={Math.ceil(scans.length / rowsPerPage)}
                page={page}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
