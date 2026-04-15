import React, { useState, useCallback, useMemo } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Add from "@mui/icons-material/Add";
import ImageSearch from "@mui/icons-material/ImageSearch";

import { useFeedManagement } from "../hooks/api/useFeedManagementApi";
import { useIconManagement } from "../hooks/api/useIconManagement";
import { useNotification } from "../../../core/hooks/ui/useNotification";
import NotificationSnackbar from "../components/ui/NotificationSnackbar";
import ConfirmDeleteDialog from "../../../core/components/ui/ConfirmDeleteDialog";
import AddFeedDialog from "./components/modals/AddFeedDialog";
import FeedListItem from "./components/ui/FeedListItem";

export default function ManageNewsfeeds() {
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [bulkRefetchLoading, setBulkRefetchLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [feedToDelete, setFeedToDelete] = useState(null);

  const { feeds, setFeeds, loading, toggleFeed, addFeed, deleteFeed } = useFeedManagement();
  const { deleteIcon, processIconFile, refetchIcon, refetchAllMissingIcons } = useIconManagement(feeds, setFeeds);
  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const feedEntries = useMemo(() => Object.entries(feeds), [feeds]);
  const hasMissingIcons = useMemo(
    () => Object.values(feeds).some((feed) => feed.icon === "default.png" || !feed.icon_id),
    [feeds]
  );

  const handleFeedAdd = useCallback(async ({ name, url, iconFile }) => {
    const result = await addFeed({ name, url }, iconFile);
    if (result.success) showSuccess("Feed added successfully");
    return result;
  }, [addFeed, showSuccess]);

  const handleToggle = useCallback(async (feedName) => {
    const result = await toggleFeed(feedName);
    if (result.success) {
      showSuccess(`Feed ${result.enabled ? "enabled" : "disabled"} successfully`);
    } else {
      showError("Failed to toggle feed");
    }
  }, [toggleFeed, showSuccess, showError]);

  const handleDelete = useCallback((name) => {
    setFeedToDelete(name);
    setDeleteDialogOpen(true);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    setDeleteDialogOpen(false);
    const result = await deleteFeed(feedToDelete);
    setFeedToDelete(null);
    if (result.success) {
      showSuccess("Feed deleted successfully");
    } else {
      showError("Error deleting feed");
    }
  }, [deleteFeed, feedToDelete, showSuccess, showError]);

  const handleIconDelete = useCallback(async (feedName) => {
    const result = await deleteIcon(feedName);
    if (result.success) {
      showSuccess(result.message || "Icon deleted successfully");
    } else {
      showError(result.error?.response?.data?.detail || "Error deleting icon");
    }
  }, [deleteIcon, showSuccess, showError]);

  const handleRefetchIcon = useCallback(async (feedName) => {
    const result = await refetchIcon(feedName);
    if (result.success) {
      showSuccess(result.message || "Icon refreshed");
    } else {
      showError(result.message || result.error?.response?.data?.detail || "Failed to refresh icon");
    }
  }, [refetchIcon, showSuccess, showError]);

  const handleBulkRefetch = useCallback(async () => {
    setBulkRefetchLoading(true);
    const result = await refetchAllMissingIcons();
    setBulkRefetchLoading(false);
    if (result.success) {
      if (result.succeeded > 0) {
        showSuccess(`Fetched ${result.succeeded} of ${result.total} missing icons`);
      } else {
        showError("No favicons could be downloaded");
      }
    } else {
      showError("Error fetching missing icons");
    }
  }, [refetchAllMissingIcons, showSuccess, showError]);

  return (
    <Card sx={{ borderRadius: 1, boxShadow: 1, p: 2, maxWidth: "100%", height: "90vh", display: "flex", flexDirection: "column" }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h6" component="h2">Manage Newsfeeds</Typography>
        <Stack direction="row" spacing={1}>
          <Tooltip title={hasMissingIcons ? "Fetch favicons for feeds with missing icons" : "All feeds have icons"}>
            <span>
              <Button
                variant="outlined"
                size="small"
                startIcon={bulkRefetchLoading ? <CircularProgress size={16} /> : <ImageSearch />}
                onClick={handleBulkRefetch}
                disabled={bulkRefetchLoading || !hasMissingIcons}
              >
                Fetch Missing Icons
              </Button>
            </span>
          </Tooltip>
          <Button variant="contained" size="small" startIcon={<Add />} onClick={() => setAddDialogOpen(true)}>
            Add Feed
          </Button>
        </Stack>
      </Stack>

      <Divider />

      <List dense sx={{ flex: 1, overflow: "auto", mt: 1, "& ul": { padding: 0 } }}>
        {loading ? (
          <Box display="flex" justifyContent="center" p={2}>
            <CircularProgress size={24} />
          </Box>
        ) : feedEntries.length === 0 ? (
          <Box display="flex" justifyContent="center" alignItems="center" p={4}>
            <Typography variant="body2" color="text.secondary">
              No feeds configured. Click "Add Feed" to get started.
            </Typography>
          </Box>
        ) : (
          feedEntries.map(([name, feed], index) => (
            <React.Fragment key={name}>
              <FeedListItem
                name={name}
                feed={feed}
                onToggle={handleToggle}
                onDelete={handleDelete}
                onIconDelete={handleIconDelete}
                onRefetchIcon={handleRefetchIcon}
              />
              {index < feedEntries.length - 1 && <Divider variant="inset" component="li" />}
            </React.Fragment>
          ))
        )}
      </List>

      <AddFeedDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onSubmit={handleFeedAdd}
        processIconFile={processIconFile}
      />

      <NotificationSnackbar
        open={notification.open}
        message={notification.message}
        severity={notification.severity}
        onClose={hideNotification}
      />

      <ConfirmDeleteDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Feed"
        message="Are you sure you want to delete this feed? This action cannot be undone."
      />
    </Card>
  );
}
