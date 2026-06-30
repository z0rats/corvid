import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import SecurityIcon from '@mui/icons-material/Security';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import StorageIcon from '@mui/icons-material/Storage';
import WebIcon from '@mui/icons-material/Web';
import SearchIcon from '@mui/icons-material/Search';
import ListAltIcon from '@mui/icons-material/ListAlt';

import GeneralInfo from '../../GeneralInfo';
import NoDetails from '../NoDetails';

const CharacteristicItem = ({ icon, primary, secondary, yes, no, notAvailable }) => (
  <ListItem dense disableGutters>
    <ListItemIcon sx={{minWidth: 36}}>{icon}</ListItemIcon>
    <ListItemText
      primary={primary}
      secondary={typeof secondary === 'boolean' ? (secondary ? yes : no) : (secondary || notAvailable)}
      primaryTypographyProps={{ variant: 'body2' }}
      secondaryTypographyProps={{ variant: 'body2', color: 'text.secondary' }}
    />
  </ListItem>
);


export default function MaltiverseDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const yes = t('providers.common.yes');
  const no = t('providers.common.no');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (!result || result.error) {
    const message = result && result.error
        ? t('providers.maltiverse.errorFetching', { error: result.message || result.error })
        : t('providers.maltiverse.unavailable');
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={message} />
      </Box>
    );
  }
  if (!result.classification && !result.ip_addr) {
      return (
         <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
            <NoDetails message={t('providers.maltiverse.insufficientData')} />
        </Box>
      )
  }


  const transformedData = {
    ip: result.ip_addr || ioc,
    countryCode: result.country_code,
    city: result.city,
    isp: result.isp || result.as_name,
    organization: result.organization,
  };

  const blacklistEntries = Array.isArray(result.blacklist) ? result.blacklist : [];

  const ipCharacteristics = (
    <Card sx={{ flex: 1, p: 2, borderRadius: 1, boxShadow: 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <SecurityIcon />
        <Typography variant="h6" component="h2">{t('providers.maltiverse.threatProfileAndIpCharacteristics')}</Typography>
      </Box>
      <List dense>
        <CharacteristicItem icon={<SecurityIcon color="action" />} primary={t('providers.maltiverse.classification')} secondary={result.classification} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<VpnKeyIcon color="action" />} primary={t('providers.maltiverse.vpnNode')} secondary={result.is_vpn_node} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<VpnKeyIcon color="action" />} primary={t('providers.maltiverse.openProxy')} secondary={result.is_open_proxy} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<VpnKeyIcon color="action" />} primary={t('providers.maltiverse.torNode')} secondary={result.is_tor_node} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<NetworkCheckIcon color="action" />} primary={t('providers.maltiverse.cnc')} secondary={result.is_cnc} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<NetworkCheckIcon color="action" />} primary={t('providers.maltiverse.distributingMalware')} secondary={result.is_distributing_malware} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<StorageIcon color="action" />} primary={t('providers.maltiverse.cdnNode')} secondary={result.is_cdn} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<StorageIcon color="action" />} primary={t('providers.maltiverse.hostingService')} secondary={result.is_hosting} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<WebIcon color="action" />} primary={t('providers.maltiverse.webServer')} secondary={result.is_web_server} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<WebIcon color="action" />} primary={t('providers.maltiverse.webHosting')} secondary={result.is_web_hosting} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<SearchIcon color="action" />} primary={t('providers.maltiverse.knownScanner')} secondary={result.is_known_scanner} yes={yes} no={no} notAvailable={notAvailable} />
        <CharacteristicItem icon={<SearchIcon color="action" />} primary={t('providers.maltiverse.webSpider')} secondary={result.is_web_spider} yes={yes} no={no} notAvailable={notAvailable} />
      </List>
    </Card>
  );

  const blacklistDetailsTable = blacklistEntries.length > 0 && (
    <Card sx={{ mt: 2, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Grid container spacing={1} alignItems="center" mb={1}>
            <ListAltIcon color="action" />
            <Typography variant="h6" component="div" sx={{ ml: 1 }}>
                {t('providers.maltiverse.blacklistMentions', { count: blacklistEntries.length })}
            </Typography>
        </Grid>
        <TableContainer component={Paper} sx={{ borderRadius: 1 }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell sx={{fontWeight:'bold', bgcolor:'background.paper'}}>{t('providers.maltiverse.columns.description')}</TableCell>
                <TableCell sx={{fontWeight:'bold', bgcolor:'background.paper'}}>{t('providers.maltiverse.columns.firstSeen')}</TableCell>
                <TableCell sx={{fontWeight:'bold', bgcolor:'background.paper'}}>{t('providers.maltiverse.columns.lastSeen')}</TableCell>
                <TableCell sx={{fontWeight:'bold', bgcolor:'background.paper'}}>{t('providers.maltiverse.columns.source')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {blacklistEntries
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((entry, index) => (
                  <TableRow hover key={`${entry.source}-${entry.first_seen}-${index}`}>
                    <TableCell sx={{wordBreak:'break-word'}}>{entry.description}</TableCell>
                    <TableCell>{entry.first_seen ? new Date(entry.first_seen).toLocaleDateString() : notAvailable}</TableCell>
                    <TableCell>{entry.last_seen ? new Date(entry.last_seen).toLocaleDateString() : notAvailable}</TableCell>
                    <TableCell sx={{wordBreak:'break-word'}}>{entry.source}</TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={blacklistEntries.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            sx={{borderTop: '1px solid', borderColor: 'divider', mt:0}}
        />
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Grid container spacing={2} alignItems="stretch">
        <Grid size={{ xs: 12, md: 5 }} sx={{ display: 'flex' }}>
          <Box sx={{ flex: 1 }}>
            <GeneralInfo data={transformedData} />
          </Box>
        </Grid>
        <Grid size={{ xs: 12, md: 7 }} sx={{ display: 'flex' }}>
          {ipCharacteristics}
        </Grid>
      </Grid>
      {blacklistEntries.length > 0 && (
        <Box mt={2}>
            {blacklistDetailsTable}
        </Box>
      )}
      {blacklistEntries.length === 0 && result.classification && (
         <Card sx={{ mt: 2, borderRadius: 1, boxShadow: 0 }}>
            <CardContent sx={{textAlign:'center'}}>
                <ListAltIcon color="action" sx={{fontSize: 30, mb:1}}/>
                <Typography variant="body1" color="text.secondary">{t('providers.maltiverse.noBlacklistEntries')}</Typography>
            </CardContent>
         </Card>
      )}
    </Box>
  );
}
