import React, { useState, useCallback } from "react";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Tooltip from "@mui/material/Tooltip";
import Delete from "@mui/icons-material/Delete";
import DeleteOutline from "@mui/icons-material/DeleteOutline";
import Refresh from "@mui/icons-material/Refresh";

import { getFeedIconUrl } from "../../../utils/urlUtils";

const hasCustomIcon = (feed) => feed.icon !== "default.png" && feed.icon_id;

function FeedListItem({ name, feed, onToggle, onDelete, onIconDelete, onRefetchIcon }) {
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
      secondaryAction={
        <Stack direction="row" spacing={0.5} alignItems="center">
          <Tooltip title="Refresh favicon">
            <span>
              <IconButton
                onClick={handleRefetch}
                disabled={refetchLoading}
                aria-label="Refresh icon"
              >
                {refetchLoading ? <CircularProgress size={20} /> : <Refresh />}
              </IconButton>
            </span>
          </Tooltip>

          <Switch checked={feed.enabled} onChange={() => onToggle(name)} size="small" />

          <Tooltip title="Delete feed">
            <IconButton
              color="error"
              onClick={() => onDelete(name)}
              aria-label="Delete feed"
            >
              <Delete />
            </IconButton>
          </Tooltip>
        </Stack>
      }
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
            <Tooltip title="Remove custom icon">
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
        primary={name}
        secondary={feed.url}
        primaryTypographyProps={{ variant: "body2", fontWeight: 500 }}
        secondaryTypographyProps={{
          variant: "caption",
          noWrap: true,
          sx: { maxWidth: 300 },
        }}
      />
    </ListItem>
  );
}

export default React.memo(FeedListItem);
