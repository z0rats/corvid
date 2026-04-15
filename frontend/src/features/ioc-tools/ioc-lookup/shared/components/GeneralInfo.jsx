import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import RouterIcon from '@mui/icons-material/Router';
import LanguageIcon from '@mui/icons-material/Language';
import DomainIcon from '@mui/icons-material/Domain';
import PublicIcon from '@mui/icons-material/Public';
import BusinessIcon from '@mui/icons-material/Business';
import DnsIcon from '@mui/icons-material/Dns';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import StorageIcon from '@mui/icons-material/Storage';
import LocationCityIcon from '@mui/icons-material/LocationCity';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';


const GeneralInfo = ({
  data = {},
  loading = false,
  error = null,
}) => {
  if (loading) return <Typography>Loading...</Typography>;
  if (error) return <Typography color="error">Error loading information</Typography>;

  const {
    ip,
    ipType,
    ipRange,
    reverseDns,
    domain,
    hostnames = [],
    type,
    country,
    countryCode,
    region,
    city,
    organisation,
    isp,
    asn = {},
  } = data;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <InfoIcon />
          <Typography variant="h6" component="h2">General Information</Typography>
        </Box>
        {/* Network Information */}
        <Typography variant="subtitle2" color="text.secondary" sx={{ pl: 2, pb: 0.5 }}>Network Information</Typography>
        <List disablePadding>
          <ListItem dense>
            <ListItemIcon>
              <RouterIcon color="action" />
            </ListItemIcon>
            <ListItemText primary="IP" secondary={ip} />
          </ListItem>
          <ListItem dense>
            <ListItemIcon>
              <RouterIcon color="action" />
            </ListItemIcon>
            <ListItemText primary="IP Type" secondary={ipType} />
          </ListItem>
          {ipRange && (
            <ListItem dense>
              <ListItemIcon>
                <RouterIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="IP Range" secondary={ipRange} />
            </ListItem>
          )}
          {reverseDns && (
            <ListItem dense>
              <ListItemIcon>
                <DnsIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Reverse DNS" secondary={reverseDns} />
            </ListItem>
          )}
        </List>

        {/* Domain Information */}
        <Divider sx={{ my: 0.5 }} />
        <Typography variant="subtitle2" color="text.secondary" sx={{ pl: 2, py: 0.5 }}>Domain Information</Typography>
        <List disablePadding>
          {domain && (
            <ListItem dense>
              <ListItemIcon>
                <DomainIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Domain" secondary={domain} />
            </ListItem>
          )}
          {hostnames?.length > 0 && (
            <ListItem dense>
              <ListItemIcon>
                <DnsIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Hostnames" secondary={hostnames.join(", ")} />
            </ListItem>
          )}
          {type && (
            <ListItem dense>
              <ListItemIcon>
                <StorageIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Type" secondary={type} />
            </ListItem>
          )}
        </List>

        {/* Location Information */}
        <Divider sx={{ my: 0.5 }} />
        <Typography variant="subtitle2" color="text.secondary" sx={{ pl: 2, py: 0.5 }}>Location Information</Typography>
        <List disablePadding>
          {country && (
            <ListItem dense>
              <ListItemIcon>
                <PublicIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Country" secondary={country} />
            </ListItem>
          )}
          {countryCode && (
            <ListItem dense>
              <ListItemIcon>
                <PublicIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Country Code" secondary={countryCode} />
            </ListItem>
          )}
          {region && (
            <ListItem dense>
              <ListItemIcon>
                <LocationCityIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Region" secondary={region} />
            </ListItem>
          )}
          {city && (
            <ListItem dense>
              <ListItemIcon>
                <LocationCityIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="City" secondary={city} />
            </ListItem>
          )}
        </List>

        {/* Organization Information */}
        <Divider sx={{ my: 0.5 }} />
        <Typography variant="subtitle2" color="text.secondary" sx={{ pl: 2, py: 0.5 }}>Organization Information</Typography>
        <List disablePadding>
          {organisation && (
            <ListItem dense>
              <ListItemIcon>
                <BusinessIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="Organisation" secondary={organisation} />
            </ListItem>
          )}
          {isp && (
            <ListItem dense>
              <ListItemIcon>
                <LanguageIcon color="action" />
              </ListItemIcon>
              <ListItemText primary="ISP" secondary={isp} />
            </ListItem>
          )}
        </List>

        {/* ASN Information */}
        {asn && Object.keys(asn).length > 0 && (
          <>
            <Divider sx={{ my: 0.5 }} />
            <Accordion
              sx={{
                '&:before': { display: 'none' },
                boxShadow: 'none',
                borderRadius: 1,
              }}
              defaultExpanded
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{ p: 0, minHeight: 36 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <NetworkCheckIcon color="action" sx={{ mr: 1 }} />
                  <Typography variant="subtitle2" color="text.secondary">ASN Information</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0 }}>
                <List disablePadding>
                  {asn.asn && (
                    <ListItem dense>
                      <ListItemIcon>
                        <NetworkCheckIcon color="action" />
                      </ListItemIcon>
                      <ListItemText primary="ASN" secondary={asn.asn} />
                    </ListItem>
                  )}
                  {asn.asOwner && (
                    <ListItem dense>
                      <ListItemIcon>
                        <BusinessIcon color="action" />
                      </ListItemIcon>
                      <ListItemText primary="AS Owner" secondary={asn.asOwner} />
                    </ListItem>
                  )}
                  {asn.asnCidr && (
                    <ListItem dense>
                      <ListItemIcon>
                        <RouterIcon color="action" />
                      </ListItemIcon>
                      <ListItemText primary="ASN CIDR" secondary={asn.asnCidr} />
                    </ListItem>
                  )}
                  {asn.asnCountryCode && (
                    <ListItem dense>
                      <ListItemIcon>
                        <PublicIcon color="action" />
                      </ListItemIcon>
                      <ListItemText primary="ASN Country" secondary={asn.asnCountryCode} />
                    </ListItem>
                  )}
                  {asn.asnDate && (
                    <ListItem dense>
                      <ListItemIcon>
                        <StorageIcon color="action" />
                      </ListItemIcon>
                      <ListItemText primary="ASN Date" secondary={asn.asnDate} />
                    </ListItem>
                  )}
                  {asn.asnRegistry && (
                    <ListItem dense>
                      <ListItemIcon>
                        <StorageIcon color="action" />
                      </ListItemIcon>
                      <ListItemText primary="ASN Registry" secondary={asn.asnRegistry} />
                    </ListItem>
                  )}
                </List>
              </AccordionDetails>
            </Accordion>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default GeneralInfo;