import React, { useState, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import Add from "@mui/icons-material/AddOutlined";
import ImageSearch from "@mui/icons-material/ImageSearchOutlined";

import { useFeedManagement } from "../hooks/api/useFeedManagementApi";
import { useIconManagement } from "../hooks/api/useIconManagement";
import { useNotification } from "../../../core/hooks/ui/useNotification";
import NotificationSnackbar from "../components/ui/NotificationSnackbar";
import ConfirmDeleteDialog from "../../../core/components/ui/ConfirmDeleteDialog";
import AddFeedDialog from "./components/modals/AddFeedDialog";
import FeedListItem from "./components/ui/FeedListItem";

export default function ManageNewsfeeds() {
  const { t } = useTranslation('newsfeed');
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
    if (result.success) showSuccess(t('settings.feeds.feedAddedSuccess'));
    return result;
  }, [addFeed, showSuccess, t]);

  const handleToggle = useCallback(async (feedName) => {
    const result = await toggleFeed(feedName);
    if (result.success) {
      showSuccess(result.enabled ? t('settings.feeds.feedEnabledSuccess') : t('settings.feeds.feedDisabledSuccess'));
    } else {
      showError(t('settings.feeds.feedToggleError'));
    }
  }, [toggleFeed, showSuccess, showError, t]);

  const handleDelete = useCallback((name) => {
    setFeedToDelete(name);
    setDeleteDialogOpen(true);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    setDeleteDialogOpen(false);
    const result = await deleteFeed(feedToDelete);
    setFeedToDelete(null);
    if (result.success) {
      showSuccess(t('settings.feeds.feedDeletedSuccess'));
    } else {
      showError(t('settings.feeds.feedDeleteError'));
    }
  }, [deleteFeed, feedToDelete, showSuccess, showError, t]);

  const handleIconDelete = useCallback(async (feedName) => {
    const result = await deleteIcon(feedName);
    if (result.success) {
      showSuccess(result.message || t('settings.feeds.iconDeletedSuccess'));
    } else {
      showError(result.error?.response?.data?.detail || t('settings.feeds.iconDeleteError'));
    }
  }, [deleteIcon, showSuccess, showError, t]);

  const handleRefetchIcon = useCallback(async (feedName) => {
    const result = await refetchIcon(feedName);
    if (result.success) {
      showSuccess(result.message || t('settings.feeds.iconRefreshedSuccess'));
    } else {
      showError(result.message || result.error?.response?.data?.detail || t('settings.feeds.iconRefreshError'));
    }
  }, [refetchIcon, showSuccess, showError, t]);

  const handleBulkRefetch = useCallback(async () => {
    setBulkRefetchLoading(true);
    const result = await refetchAllMissingIcons();
    setBulkRefetchLoading(false);
    if (result.success) {
      if (result.succeeded > 0) {
        showSuccess(t('settings.feeds.bulkFetchSuccess', { succeeded: result.succeeded, total: result.total }));
      } else {
        showError(t('settings.feeds.bulkFetchNoneError'));
      }
    } else {
      showError(t('settings.feeds.bulkFetchError'));
    }
  }, [refetchAllMissingIcons, showSuccess, showError, t]);

  return (
    <Card sx={{ borderRadius: 1, boxShadow: 1, p: 2, maxWidth: "100%", height: "90vh", display: "flex", flexDirection: "column" }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Typography variant="h6" component="h2">{t('settings.feeds.title')}</Typography>
        <Stack direction="row" spacing={1}>
          <Tooltip title={hasMissingIcons ? t('settings.feeds.fetchMissingIconsTooltip') : t('settings.feeds.allFeedsHaveIcons')}>
            <span>
              <Button
                variant="outlined"
                size="small"
                startIcon={bulkRefetchLoading ? <CircularProgress size={16} /> : <ImageSearch />}
                onClick={handleBulkRefetch}
                disabled={bulkRefetchLoading || !hasMissingIcons}
              >
                {t('settings.feeds.fetchMissingIcons')}
              </Button>
            </span>
          </Tooltip>
          <Button variant="contained" size="small" startIcon={<Add />} onClick={() => setAddDialogOpen(true)}>
            {t('settings.feeds.addFeed')}
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
              {t('settings.feeds.noFeedsConfigured')}
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
        title={t('settings.feeds.deleteDialogTitle')}
        message={t('settings.feeds.deleteDialogMessage')}
      />
    </Card>
  );
}
