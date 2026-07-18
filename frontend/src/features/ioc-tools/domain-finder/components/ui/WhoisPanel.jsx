import React from "react";
import { useTranslation } from 'react-i18next';
import { useWhoisLookup } from "../../hooks/api/useWhoisLookup";
import { domainUtils } from "../../utils/domainUtils";

import Alert from '@mui/material/Alert';
import ApartmentIcon from "@mui/icons-material/Apartment";
import BadgeIcon from "@mui/icons-material/Badge";
import BusinessIcon from "@mui/icons-material/Business";
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import DnsIcon from "@mui/icons-material/Dns";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import EventBusyIcon from "@mui/icons-material/EventBusy";
import Grid from '@mui/material/Grid';
import LabelIcon from "@mui/icons-material/Label";
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import UpdateIcon from "@mui/icons-material/Update";

function Field({ icon, label, value, t }) {
  return (
    <ListItem>
      <ListItemIcon>{icon}</ListItemIcon>
      <ListItemText primary={label} secondary={value || t('domainFinder.details.notAvailable')} />
    </ListItem>
  );
}

export default function WhoisPanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const { data, loading, error, unsupported } = useWhoisLookup(domain);

  if (unsupported) {
    return (
      <Alert severity="info" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
        {t('domainFinder.whois.unsupportedPattern')}
      </Alert>
    );
  }

  if (loading) {
    return (
      <>
        <LinearProgress />
        <br />
      </>
    );
  }

  if (error) {
    return (
      <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
        {t('domainFinder.whois.errorPrefix')} {error}
      </Alert>
    );
  }

  if (!data) return null;

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.whois.title')}
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <List dense>
              <Field
                t={t}
                icon={<ApartmentIcon />}
                label={t('domainFinder.whois.fields.registrar')}
                value={data.registrar}
              />
              <Field
                t={t}
                icon={<BadgeIcon />}
                label={t('domainFinder.whois.fields.registrarIanaId')}
                value={data.registrar_iana_id}
              />
              <Field
                t={t}
                icon={<BusinessIcon />}
                label={t('domainFinder.whois.fields.registrantOrganization')}
                value={data.registrant_organization}
              />
            </List>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <List dense>
              <Field
                t={t}
                icon={<EventAvailableIcon />}
                label={t('domainFinder.whois.fields.creationDate')}
                value={domainUtils.formatDate(data.creation_date)}
              />
              <Field
                t={t}
                icon={<EventBusyIcon />}
                label={t('domainFinder.whois.fields.expirationDate')}
                value={domainUtils.formatDate(data.expiration_date)}
              />
              <Field
                t={t}
                icon={<UpdateIcon />}
                label={t('domainFinder.whois.fields.updatedDate')}
                value={domainUtils.formatDate(data.updated_date)}
              />
            </List>
          </Grid>
        </Grid>

        {data.statuses?.length > 0 && (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ mt: 1, gap: 1 }}>
            <LabelIcon fontSize="small" color="action" />
            {data.statuses.map((status) => (
              <Chip key={status} label={status} size="small" variant="outlined" />
            ))}
          </Stack>
        )}

        {data.nameservers?.length > 0 && (
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" sx={{ mt: 1, gap: 1 }}>
            <DnsIcon fontSize="small" color="action" />
            {data.nameservers.map((ns) => (
              <Chip key={ns} label={ns} size="small" variant="outlined" />
            ))}
          </Stack>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('domainFinder.whois.sourceLabel')} {data.rdap_server}
        </Typography>
      </CardContent>
    </Card>
  );
}
