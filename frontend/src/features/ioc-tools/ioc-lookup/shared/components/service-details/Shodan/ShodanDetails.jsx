import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import BusinessIcon from '@mui/icons-material/Business';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';
import TagIcon from '@mui/icons-material/Label';
import DomainIcon from '@mui/icons-material/Language';
import LocationIcon from '@mui/icons-material/LocationCity';
import PublicIcon from '@mui/icons-material/Public';
import PortIcon from '@mui/icons-material/Router';
import SecurityIcon from '@mui/icons-material/Security';
import DataIcon from '@mui/icons-material/Storage';

import NoDetails from '../NoDetails';

const CollapsibleSection = ({ title, icon: Icon, children, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <Box sx={{ mb: 1 }}>
      <ListItemButton onClick={() => setExpanded(!expanded)} sx={{ borderRadius: 1, py: 0.5, px:1 }}>
        <ListItemIcon sx={{minWidth: 36}}>
          <Icon color="action" />
        </ListItemIcon>
        <ListItemText primary={title} primaryTypographyProps={{variant: 'subtitle1', fontWeight:'medium'}}/>
        {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </ListItemButton>
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box sx={{ pt: 1, pb:1, pl: 2, pr: 1 }}>
          {children}
        </Box>
      </Collapse>
      <Divider sx={{mt:1}}/>
    </Box>
  );
};

const DataDisplay = ({ data, level = 0 }) => {
  if (typeof data === 'object' && data !== null) {
    if (level === 1 && data.location && typeof data.location === 'object') {
        const { location, ...restOfData } = data;
        return (
            <>
                {Object.entries(location).map(([key, value]) => (
                     <ListItem key={`loc-${key}`} sx={{ flexDirection: 'column', alignItems: 'flex-start', width: '100%', py:0.2, pl: level > 0 ? 1 : 0 }}>
                        <Typography variant="caption" color="text.secondary" sx={{fontWeight:'medium'}}>
                        location.{key}:
                        </Typography>
                        <Box sx={{ pl: 1, width: '100%', overflowWrap: 'break-word' }}>
                            <Typography variant="caption" sx={{ wordBreak: 'break-all' }}>{String(value)}</Typography>
                        </Box>
                    </ListItem>
                ))}
                <DataDisplay data={restOfData} level={level +1} />
            </>
        );
    }


    return (
      <List dense disablePadding sx={{ width: '100%', overflowX: 'hidden' }}>
        {Object.entries(data).map(([key, value]) => (
          <ListItem key={key} sx={{ flexDirection: 'column', alignItems: 'flex-start', width: '100%', py:0.2, pl: level > 0 ? 1 : 0 }}>
            <Typography variant="caption" color="text.secondary" sx={{fontWeight:'medium', textTransform: 'capitalize'}}>
              {key.replace(/_/g, ' ')}:
            </Typography>
            <Box sx={{ pl: 1, width: '100%', overflowWrap: 'break-word' }}>
              {typeof value === 'object' && value !== null && !Array.isArray(value) ? (
                <DataDisplay data={value} level={level + 1} />
              ) : Array.isArray(value) ? (
                <Typography variant="caption" sx={{ wordBreak: 'break-all' }}>{value.join(', ')}</Typography>
              ) : (
                <Typography variant="caption" sx={{ wordBreak: 'break-all' }}>{String(value)}</Typography>
              )}
            </Box>
          </ListItem>
        ))}
      </List>
    );
  }
  return <Typography variant="caption" sx={{ wordBreak: 'break-all' }}>{String(data)}</Typography>;
};


export default function ShodanDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');

  if (!result) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.shodan.loading')} />
      </Box>
    );
  }

  if (result.shodan_error || result.error) {
    const errorMessage = result.shodan_error || (result.error ? (result.message || result.error) : t('providers.shodan.unknownError'));
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.shodan.errorFetching', { error: errorMessage })} />
      </Box>
    );
  }

  if (result.error === "No information available" || (Object.keys(result).length === 1 && result.ip_str && !result.ports && !result.data )) {
     return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.shodan.noInfoFound', { ip: result.ip_str || ioc })} />
      </Box>
    );
  }


  const generalInfo = (
    <List dense>
      <ListItem>
        <ListItemIcon sx={{minWidth:36}}><LocationIcon color="action" /></ListItemIcon>
        <ListItemText
          primary={t('providers.shodan.location')}
          secondary={[
            result.city,
            result.region_code,
            result.country_name,
            result.postal_code
          ].filter(Boolean).join(', ') || notAvailable}
        />
      </ListItem>
      <ListItem>
        <ListItemIcon sx={{minWidth:36}}><BusinessIcon color="action" /></ListItemIcon>
        <ListItemText
          primary={t('providers.shodan.organizationAsn')}
          secondary={`${result.org || notAvailable} (${result.asn || notAvailable})`}
        />
      </ListItem>
      <ListItem>
        <ListItemIcon sx={{minWidth:36}}><PublicIcon color="action" /></ListItemIcon>
        <ListItemText
          primary={t('providers.shodan.isp')}
          secondary={result.isp || notAvailable}
        />
      </ListItem>
       <ListItem>
        <ListItemIcon sx={{minWidth:36}}><DomainIcon color="action" /></ListItemIcon>
        <ListItemText
          primary={t('providers.shodan.lastUpdate')}
          secondary={result.last_update ? new Date(result.last_update).toLocaleString() : notAvailable}
        />
      </ListItem>
    </List>
  );

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Card sx={{ borderRadius: 1, boxShadow: 0 }}>
        <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <InfoIcon />
                <Typography variant="h6" component="div">
                {t('providers.shodan.ipReportFor')} <Typography component="span" sx={{wordBreak: 'break-all'}}>{result.ip_str || ioc}</Typography>
                </Typography>
            </Box>

            {generalInfo}
            <Divider sx={{ my: 1 }} />

            {result.ports?.length > 0 && (
                <CollapsibleSection title={t('providers.shodan.openPorts', { count: result.ports.length })} icon={PortIcon} defaultExpanded>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {result.ports.map((port) => (
                    <Chip key={port} label={port} size="small" variant="outlined" sx={{borderRadius:1}} />
                    ))}
                </Box>
                </CollapsibleSection>
            )}

            {(result.domains?.length > 0 || result.hostnames?.length > 0) && (
                <CollapsibleSection title={t('providers.shodan.domainsAndHostnames')} icon={DomainIcon} defaultExpanded>
                {result.domains?.length > 0 && (
                    <Box sx={{ mb: result.hostnames?.length > 0 ? 1: 0, mt: 0.5 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>{t('providers.shodan.domainsCount', { count: result.domains.length })}</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {result.domains.map((domain) => ( <Chip key={`dom-${domain}`} label={domain} size="small" variant="outlined" /> ))}
                    </Box>
                    </Box>
                )}

                {result.hostnames?.length > 0 && (
                    <Box sx={{mt: 0.5}}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>{t('providers.shodan.hostnamesCount', { count: result.hostnames.length })}</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {result.hostnames.map((hostname) => ( <Chip key={`host-${hostname}`} label={hostname} size="small" variant="outlined" /> ))}
                    </Box>
                    </Box>
                )}
                </CollapsibleSection>
            )}

            {result.tags?.length > 0 && (
                <CollapsibleSection title={t('providers.shodan.tagsCount', { count: result.tags.length })} icon={TagIcon}>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {result.tags.map((tag) => ( <Chip key={`tag-${tag}`} label={tag} size="small" variant="filled" color="secondary" sx={{borderRadius:1}}/> ))}
                </Box>
                </CollapsibleSection>
            )}

            {result.data?.length > 0 && (
                <CollapsibleSection title={t('providers.shodan.serviceBanners', { count: result.data.length })} icon={DataIcon}>
                {result.data.map((item, idx) => (
                    <Card key={`${item.port}-${item.transport}-${idx}`} sx={{ mb: 1, mt:0.5, boxShadow: 0 }}>
                        <CardContent sx={{p:1, '&:last-child': {pb:1}}}>
                            <DataDisplay data={item} />
                        </CardContent>
                    </Card>
                ))}
                </CollapsibleSection>
            )}

            {result.vulns?.length > 0 && (
                 <CollapsibleSection title={t('providers.shodan.vulnerabilities', { count: result.vulns.length })} icon={SecurityIcon} defaultExpanded>
                    <List dense disablePadding>
                        {result.vulns.map((vuln_id) => (
                            <ListItem key={vuln_id} dense disableGutters>
                                <ListItemText primary={vuln_id} primaryTypographyProps={{variant:'body2', color:'error.main'}}/>
                            </ListItem>
                        ))}
                    </List>
                 </CollapsibleSection>
            )}


        </CardContent>
      </Card>
    </Box>
  );
}
