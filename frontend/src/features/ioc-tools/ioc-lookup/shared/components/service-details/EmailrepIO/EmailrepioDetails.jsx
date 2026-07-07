import React from "react";
import { useTranslation } from 'react-i18next';

import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import ContactsIcon from "@mui/icons-material/Contacts";
import FacebookIcon from "@mui/icons-material/Facebook";
import Grid from "@mui/material/Grid";
import InfoIcon from "@mui/icons-material/Info";
import InstagramIcon from "@mui/icons-material/Instagram";
import LinkedInIcon from "@mui/icons-material/LinkedIn";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import ListItemText from "@mui/material/ListItemText";
import PersonIcon from "@mui/icons-material/Person";
import PinterestIcon from "@mui/icons-material/Pinterest";
import RedditIcon from "@mui/icons-material/Reddit";
import TwitterIcon from "@mui/icons-material/Twitter";
import Typography from '@mui/material/Typography';
import YouTubeIcon from "@mui/icons-material/YouTube";

import NoDetails from "../NoDetails";

const DetailListItem = ({ primaryText, secondaryText, secondaryHelperText = "", notAvailable }) => (
  <ListItem sx={{ alignItems: 'flex-start' }}>
    <ListItemText
      primary={
        <Typography variant="subtitle1" fontWeight="medium" color="text.primary">
          {primaryText}
        </Typography>
      }
      secondary={
        <>
          <Typography
            sx={{ display: "inline" }}
            component="span"
            variant="body2"
            color="text.secondary"
          >
            {secondaryText !== null && typeof secondaryText !== 'undefined' ? String(secondaryText) : notAvailable}
          </Typography>
          {secondaryHelperText && (
             <Typography component="span" variant="caption" color="text.disabled" sx={{ ml: 0.5 }}>
                {secondaryHelperText}
             </Typography>
          )}
        </>
      }
      sx={{ my: 0 }}
    />
  </ListItem>
);


export default function EmailrepioDetails({ result, ioc }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const yes = t('providers.common.yes');
  const no = t('providers.common.no');
  const yn = (value) => (value ? yes : no);

  if (!result || result.error || !result.details) {
    const message = result && result.error
        ? t('providers.emailrepio.errorFetching', { error: result.message || result.error })
        : t('providers.emailrepio.unavailable');
    return (
        <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
          <NoDetails message={message} />
        </Box>
    );
  }

  const { details, reputation, references, suspicious } = result;

  const fields = [
    { primary: t('providers.emailrepio.fields.email'), secondaryText: result.email || ioc },
    { primary: t('providers.emailrepio.fields.reputation'), secondaryText: reputation },
    { primary: t('providers.emailrepio.fields.suspicious'), secondaryText: yn(suspicious) },
    { primary: t('providers.emailrepio.fields.references'), secondaryText: references, helper: t('providers.emailrepio.helpers.references') },
    { primary: t('providers.emailrepio.fields.blacklisted'), secondaryText: yn(details.blacklisted), helper: t('providers.emailrepio.helpers.blacklisted') },
    { primary: t('providers.emailrepio.fields.maliciousActivity'), secondaryText: yn(details.malicious_activity), helper: t('providers.emailrepio.helpers.maliciousActivity') },
    { primary: t('providers.emailrepio.fields.recentMaliciousActivity'), secondaryText: yn(details.malicious_activity_recent), helper: t('providers.emailrepio.helpers.recentMaliciousActivity') },
    { primary: t('providers.emailrepio.fields.credentialsLeaked'), secondaryText: yn(details.credentials_leaked), helper: t('providers.emailrepio.helpers.credentialsLeaked') },
    { primary: t('providers.emailrepio.fields.dataBreaches'), secondaryText: yn(details.data_breach), helper: t('providers.emailrepio.helpers.dataBreaches') },
    { primary: t('providers.emailrepio.fields.firstSeen'), secondaryText: details.first_seen, helper: t('providers.emailrepio.helpers.firstSeen') },
    { primary: t('providers.emailrepio.fields.lastSeen'), secondaryText: details.last_seen, helper: t('providers.emailrepio.helpers.lastSeen') },
    { primary: t('providers.emailrepio.fields.domainExists'), secondaryText: yn(details.domain_exists) },
    { primary: t('providers.emailrepio.fields.domainReputation'), secondaryText: details.domain_reputation, helper: t('providers.emailrepio.helpers.domainReputation') },
    { primary: t('providers.emailrepio.fields.newDomain'), secondaryText: yn(details.new_domain), helper: t('providers.emailrepio.helpers.newDomain') },
    { primary: t('providers.emailrepio.fields.daysSinceDomainCreation'), secondaryText: details.days_since_domain_creation },
    { primary: t('providers.emailrepio.fields.suspiciousTld'), secondaryText: yn(details.suspicious_tld), helper: t('providers.emailrepio.helpers.suspiciousTld') },
    { primary: t('providers.emailrepio.fields.spam'), secondaryText: yn(details.spam), helper: t('providers.emailrepio.helpers.spam') },
    { primary: t('providers.emailrepio.fields.freeProvider'), secondaryText: yn(details.free_provider) },
    { primary: t('providers.emailrepio.fields.disposable'), secondaryText: yn(details.disposable), helper: t('providers.emailrepio.helpers.disposable') },
    { primary: t('providers.emailrepio.fields.deliverable'), secondaryText: yn(details.deliverable) },
    { primary: t('providers.emailrepio.fields.acceptAll'), secondaryText: yn(details.accept_all), helper: t('providers.emailrepio.helpers.acceptAll') },
    { primary: t('providers.emailrepio.fields.validMx'), secondaryText: yn(details.valid_mx) },
    { primary: t('providers.emailrepio.fields.spoofable'), secondaryText: yn(details.spoofable), helper: t('providers.emailrepio.helpers.spoofable') },
    { primary: t('providers.emailrepio.fields.spfStrict'), secondaryText: yn(details.spf_strict) },
    { primary: t('providers.emailrepio.fields.dmarcEnforced'), secondaryText: yn(details.dmarc_enforced) },
  ];

  return (
    <Box sx={{ margin: 1, mt:0 }}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider', height: '100%' }}>
            <CardContent>
              <Grid direction="row" container spacing={1} alignItems="center" mb={1}>
                <InfoIcon color="action" />
                <Typography variant="h6" component="div" sx={{ ml: 1 }}>
                  {t('providers.emailrepio.reputationAndDetails')}
                </Typography>
              </Grid>
              <List dense>
                {fields.map((field, index) => (
                  <DetailListItem
                    key={index}
                    primaryText={field.primary}
                    secondaryText={field.secondaryText}
                    secondaryHelperText={field.helper}
                    notAvailable={notAvailable}
                  />
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 5 }}>
          <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid', borderColor: 'divider', height: '100%'  }}>
            <CardContent>
                <Grid direction="row" container spacing={1} alignItems="center" mb={1}>
                    <ContactsIcon color="action"/>
                    <Typography variant="h6" component="div" sx={{ ml: 1 }}>
                        {t('providers.emailrepio.onlineProfiles')}
                    </Typography>
                </Grid>
                <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }} mb={1}>
                    {t('providers.emailrepio.onlineProfilesHelper')}
                </Typography>
                {details.profiles && details.profiles.length > 0 ? (
                    <List dense>
                    {details.profiles.map((profile, index) => (
                        <ListItem key={index}>
                        <ListItemAvatar>
                            <Avatar sx={{ bgcolor: 'primary.main' }}>
                            {profile === "facebook" ? <FacebookIcon /> :
                            profile === "instagram" ? <InstagramIcon /> :
                            profile === "linkedin" ? <LinkedInIcon /> :
                            profile === "pinterest" ? <PinterestIcon /> :
                            profile === "reddit" ? <RedditIcon /> :
                            profile === "twitter" ? <TwitterIcon /> :
                            profile === "youtube" ? <YouTubeIcon /> :
                            <PersonIcon />}
                            </Avatar>
                        </ListItemAvatar>
                        <ListItemText primaryTypographyProps={{ textTransform: 'capitalize' }} primary={profile} />
                        </ListItem>
                    ))}
                    </List>
                ) : (
                    <Typography variant="body2" color="text.secondary" sx={{mt:2}}>{t('providers.emailrepio.noProfilesFound')}</Typography>
                )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
