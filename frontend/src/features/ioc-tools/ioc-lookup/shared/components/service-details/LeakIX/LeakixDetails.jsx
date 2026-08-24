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
import DnsIcon from '@mui/icons-material/Dns';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/WarningAmber';

import NoDetails from '../NoDetails';

const CollapsibleSection = ({ title, icon: Icon, children, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <Box sx={{ mb: 1 }}>
      <ListItemButton onClick={() => setExpanded(!expanded)} sx={{ borderRadius: 1, py: 0.5, px: 1 }}>
        <ListItemIcon sx={{ minWidth: 36 }}>
          <Icon color="action" />
        </ListItemIcon>
        <ListItemText primary={title} primaryTypographyProps={{ variant: 'subtitle1', fontWeight: 'medium' }} />
        {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </ListItemButton>
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box sx={{ pt: 1, pb: 1, pl: 2, pr: 1 }}>{children}</Box>
      </Collapse>
      <Divider sx={{ mt: 1 }} />
    </Box>
  );
};

export default function LeakixDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');

  if (!result) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.leakix.loading')} />
      </Box>
    );
  }

  if (result.error) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.leakix.errorFetching', { error: result.message || result.error })} />
      </Box>
    );
  }

  const services = result.Services || [];
  const leaks = result.Leaks || [];

  if (services.length === 0 && leaks.length === 0) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={t('providers.leakix.noInfoFound', { ip: ioc })} />
      </Box>
    );
  }

  return (
    <Box sx={{ margin: 1, mt: 0 }}>
      <Card sx={{ borderRadius: 1, boxShadow: 0 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <InfoIcon />
            <Typography variant="h6" component="div">
              {t('providers.leakix.reportFor')} <Typography component="span" sx={{ wordBreak: 'break-all' }}>{ioc}</Typography>
            </Typography>
          </Box>

          {leaks.length > 0 && (
            <CollapsibleSection title={t('providers.leakix.leaksFound', { count: leaks.length })} icon={WarningIcon} defaultExpanded>
              <List dense disablePadding>
                {leaks.map((leak, idx) => (
                  <ListItem key={`leak-${idx}`} sx={{ flexDirection: 'column', alignItems: 'flex-start', width: '100%', py: 0.5 }}>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                      <Chip label={leak.type || t('providers.common.notAvailable')} size="small" color="error" variant="outlined" />
                      {leak.plugin && <Chip label={leak.plugin} size="small" variant="outlined" />}
                      {leak.port && <Chip label={`:${leak.port}`} size="small" variant="outlined" />}
                    </Box>
                    {leak.dataset && (
                      <Typography variant="caption" color="text.secondary">
                        {t('providers.leakix.datasetSummary', {
                          rows: leak.dataset.rows ?? 0,
                          databases: leak.dataset.databases ?? 0,
                        })}
                      </Typography>
                    )}
                    {leak.data && (
                      <Typography variant="caption" sx={{ wordBreak: 'break-all', display: 'block' }}>
                        {leak.data}
                      </Typography>
                    )}
                  </ListItem>
                ))}
              </List>
            </CollapsibleSection>
          )}

          {services.length > 0 && (
            <CollapsibleSection title={t('providers.leakix.servicesFound', { count: services.length })} icon={DnsIcon}>
              <List dense disablePadding>
                {services.map((service, idx) => (
                  <ListItem key={`service-${idx}`} sx={{ flexDirection: 'column', alignItems: 'flex-start', width: '100%', py: 0.5 }}>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                      <Chip label={service.type || t('providers.common.notAvailable')} size="small" variant="outlined" />
                      {service.port && <Chip label={`:${service.port}`} size="small" variant="outlined" />}
                      {service.software?.name && (
                        <Chip
                          label={`${service.software.name}${service.software.version ? ` ${service.software.version}` : ''}`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                    {service.hostname && (
                      <Typography variant="caption" color="text.secondary">{service.hostname}</Typography>
                    )}
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
