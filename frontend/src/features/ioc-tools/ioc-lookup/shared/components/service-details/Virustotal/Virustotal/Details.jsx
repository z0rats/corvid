import React from "react";
import { useTranslation } from 'react-i18next';

import AutoFixHighIcon from "@mui/icons-material/AutoFixHighOutlined";
import BusinessIcon from "@mui/icons-material/BusinessOutlined";
import ExtensionOutlinedIcon from "@mui/icons-material/ExtensionOutlined";
import GppMaybeOutlinedIcon from "@mui/icons-material/GppMaybeOutlined";
import InfoIcon from "@mui/icons-material/InfoOutlined";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import LanguageOutlinedIcon from "@mui/icons-material/LanguageOutlined";
import LanIcon from "@mui/icons-material/LanOutlined";
import RouterOutlinedIcon from "@mui/icons-material/RouterOutlined";
import CategoryOutlinedIcon from "@mui/icons-material/CategoryOutlined";

import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";

import Typography from '@mui/material/Typography';

export default function Details(props) {
  const { t } = useTranslation('iocTools');
  return (
    <Card
      sx={{
        mb: 1,
        mr: 1,
        p: 2,
        borderRadius: 1,
        boxShadow: 0,
        width: "calc(50% - 10px)",
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <InfoIcon />
        <Typography variant="h6" component="h2">{t('providers.common.generalInformation')}</Typography>
      </Box>
      <List dense>
        <ListItem alignItems="flex-start">
          <ListItemIcon>
            <GppMaybeOutlinedIcon
              color={props.malCount > 0 ? "error" : "primary"}
            />
          </ListItemIcon>
          <ListItemText
            primary={t('providers.virustotal.detectedAsMalicious', { count: props.malCount })}
          />
        </ListItem>
        {props.result["data"]["attributes"]["regional_internet_registry"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <RouterOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t('providers.virustotal.internetRegistry')}
              secondary={
                props.result["data"]["attributes"]["regional_internet_registry"]
              }
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["network"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <LanIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t('providers.virustotal.network')}
              secondary={props.result["data"]["attributes"]["network"]}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["country"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <LanguageOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t('providers.common.country')}
              secondary={props.result["data"]["attributes"]["country"]}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["as_owner"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <BusinessIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t('providers.virustotal.asOwner')}
              secondary={props.result["data"]["attributes"]["as_owner"]}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["type_extension"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <ExtensionOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t('providers.virustotal.typeExtension')}
              secondary={props.result["data"]["attributes"]["type_extension"]}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["magic"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <AutoFixHighIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t('providers.virustotal.magic')}
              secondary={props.result["data"]["attributes"]["magic"]}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["md5"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <InsertDriveFileOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary="MD5"
              secondary={props.result["data"]["attributes"]["md5"]}
              sx={{ wordBreak: "break-all" }}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["sha1"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <InsertDriveFileOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary="SHA1"
              secondary={props.result["data"]["attributes"]["sha1"]}
              sx={{ wordBreak: "break-all" }}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["sha256"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <InsertDriveFileOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary="SHA256"
              secondary={props.result["data"]["attributes"]["sha256"]}
              sx={{ wordBreak: "break-all" }}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["ssdeep"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <InsertDriveFileOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary="ssdeep"
              secondary={props.result["data"]["attributes"]["ssdeep"]}
              sx={{ wordBreak: "break-all" }}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["tlsh"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <InsertDriveFileOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary="TLSH"
              secondary={props.result["data"]["attributes"]["tlsh"]}
              sx={{ wordBreak: "break-all" }}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["vhash"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <InsertDriveFileOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary="vhash"
              secondary={props.result["data"]["attributes"]["vhash"]}
              sx={{ wordBreak: "break-all" }}
            />
          </ListItem>
        )}
        {props.result["data"]["attributes"]["unique_sources"] && (
          <ListItem alignItems="flex-start">
            <ListItemIcon>
              <CategoryOutlinedIcon color="action" />
            </ListItemIcon>
            <ListItemText
              primary={t('providers.virustotal.uniqueSources')}
              secondary={props.result["data"]["attributes"]["unique_sources"]}
            />
          </ListItem>
        )}
      </List>
    </Card>
  );
}
