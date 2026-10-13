import React, { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import ListItemText from "@mui/material/ListItemText";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Tooltip from "@mui/material/Tooltip";
import Delete from "@mui/icons-material/DeleteOutlined";
import DeleteOutline from "@mui/icons-material/DeleteOutlined";
import Refresh from "@mui/icons-material/RefreshOutlined";
import WarningAmber from "@mui/icons-material/WarningAmberOutlined";

import { getFeedIconUrl } from "../../../utils/urlUtils";
import { formatDate } from "../../../utils/formatters";
import { RELIABILITY_GRADES } from "../../../constants/reliability";

const hasCustomIcon = (feed) => feed.icon !== "default.png" && feed.icon_id;

function FeedListItem({ name, feed, onToggle, onReliabilityChange, onDelete, onIconDelete, onRefetchIcon }) {
  const { t } = useTranslation('newsfeed');
  const [refetchLoading, setRefetchLoading] = useState(false);

  const handleRefetch = useCallback(async () => {
    setRefetchLoading(true);
    await onRefetchIcon(name);
    setRefetchLoading(false);
  }, [name, onRefetchIcon]);

  return (
    <ListItem
      sx={{
        display: "flex",
        alignItems: "center",
        px: 2,
        py: 1,
        "&:hover": { backgroundColor: "action.hover" },
      }}
    >
      <ListItemAvatar>
        <Box
          sx={{
            position: "relative",
            display: "inline-block",
            "&:hover .delete-icon-overlay": hasCustomIcon(feed) ? { opacity: 1 } : {},
          }}
        >
          <Avatar
            src={getFeedIconUrl(feed.icon)}
            alt={name}
            variant="rounded"
            sx={{ width: 36, height: 36 }}
          />
          {hasCustomIcon(feed) && (
            <Tooltip title={t('settings.feeds.removeCustomIcon')}>
              <Box
                className="delete-icon-overlay"
                sx={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: "rgba(0, 0, 0, 0.6)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  opacity: 0,
                  transition: "opacity 0.2s ease-in-out",
                  cursor: "pointer",
                  borderRadius: 1,
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  onIconDelete(name);
                }}
              >
                <DeleteOutline sx={{ color: "common.white", fontSize: "1.2rem" }} />
              </Box>
            </Tooltip>
          )}
        </Box>
      </ListItemAvatar>
      <ListItemText
        primary={
          <Stack direction="row" spacing={0.5} sx={{
            alignItems: "center"
          }}>
            <span>{name}</span>
            {feed.last_error && (
              <Tooltip
                title={t('settings.feeds.fetchFailingTooltip', {
                  error: feed.last_error,
                  date: feed.last_success_at ? formatDate(feed.last_success_at) : t('settings.feeds.neverSucceeded'),
                })}
              >
                <WarningAmber color="warning" fontSize="small" />
              </Tooltip>
            )}
          </Stack>
        }
        secondary={feed.url}
        sx={{ minWidth: 0 }}
        slotProps={{
          primary: { variant: "body2", fontWeight: 500, component: "div" },
          secondary: { variant: "caption", noWrap: true, sx: { maxWidth: 300 } },
        }}
      />
      {/* In the row's flex flow, not `secondaryAction`: that is absolutely positioned and
          would overlap the name/URL once the actions outgrow the reserved right padding. */}
      <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", flexShrink: 0, ml: 1 }}>
        <Select
          value={feed.reliability ?? ""}
          onChange={(event) => onReliabilityChange(name, event.target.value)}
          displayEmpty
          size="small"
          renderValue={(value) => value || t('reliability.notRated')}
          inputProps={{ "aria-label": t('reliability.label') }}
          sx={{
            width: 112,
            fontSize: "0.8125rem",
            "& .MuiSelect-select": { py: 0.5 },
            color: feed.reliability ? "text.primary" : "text.secondary",
          }}
        >
          {RELIABILITY_GRADES.map((grade) => (
            <MenuItem key={grade} value={grade}>
              {grade} — {t(`reliability.grades.${grade}`)}
            </MenuItem>
          ))}
        </Select>

        <Tooltip title={t('settings.feeds.refreshFavicon')}>
          <span>
            <IconButton
              onClick={handleRefetch}
              disabled={refetchLoading}
              aria-label={t('settings.feeds.refreshFavicon')}
            >
              {refetchLoading ? <CircularProgress size={20} /> : <Refresh />}
            </IconButton>
          </span>
        </Tooltip>

        <Switch checked={feed.enabled} onChange={() => onToggle(name)} size="small" />

        <Tooltip title={t('settings.feeds.deleteFeed')}>
          <IconButton
            color="error"
            onClick={() => onDelete(name)}
            aria-label={t('settings.feeds.deleteFeed')}
          >
            <Delete />
          </IconButton>
        </Tooltip>
      </Stack>
    </ListItem>
  );
}

export default React.memo(FeedListItem);
