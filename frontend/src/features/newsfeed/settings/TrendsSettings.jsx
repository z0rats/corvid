import React, { useState } from "react";
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Skeleton from '@mui/material/Skeleton';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useTheme } from "@mui/material/styles";
import AddIcon from "@mui/icons-material/Add";

import { useTrendsBlacklist } from "../hooks/api/useTrendsBlacklistApi";
import { useNotification } from "../../../core/hooks/ui/useNotification";
import NotificationSnackbar from "../components/ui/NotificationSnackbar";

function BlacklistSection({ title, description, entries, newValue, onNewValueChange, onAdd, onDelete, loading }) {
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom>{title}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>{description}</Typography>

      <Box sx={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}>
        <TextField
          label={`Add ${title.toLowerCase().replace("blacklisted ", "")}`}
          value={newValue}
          size="small"
          onChange={(e) => onNewValueChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              onAdd();
            }
          }}
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={onAdd} edge="end" color="primary" sx={{ mr: "-8px" }} aria-label="Add entry">
                    <AddIcon />
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
          sx={{ mb: 2 }}
          fullWidth
        />
      </Box>

      <Box sx={{ mt: 1 }}>
        {loading ? (
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} variant="rounded" width={80} height={32} sx={{ borderRadius: 2 }} />
            ))}
          </Box>
        ) : entries.length > 0 ? (
          <Box sx={{ display: "flex", flexWrap: "wrap" }}>
            {entries.map((entry) => (
              <Chip key={entry.id} label={entry.value} onDelete={() => onDelete(entry.id)} sx={{ m: 0.5 }} />
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">No entries added yet.</Typography>
        )}
      </Box>
    </Box>
  );
}

export default function TrendsSettings() {
  const theme = useTheme();
  const [newWord, setNewWord] = useState("");
  const [newIoc, setNewIoc] = useState("");

  const {
    wordBlacklist,
    iocBlacklist,
    loading,
    addToBlacklist,
    removeFromBlacklist,
  } = useTrendsBlacklist();

  const { notification, showSuccess, showError, showWarning, hideNotification } = useNotification();

  const handleAddWord = async () => {
    if (newWord.trim() === "") return;
    const result = await addToBlacklist(newWord, "word");
    if (result.success) {
      setNewWord("");
      showSuccess("Word added to blacklist.");
    } else if (result.duplicate) {
      showWarning("Word is already blacklisted.");
    } else {
      showError("Failed to add word to blacklist.");
    }
  };

  const handleAddIoc = async () => {
    if (newIoc.trim() === "") return;
    const result = await addToBlacklist(newIoc, "ioc");
    if (result.success) {
      setNewIoc("");
      showSuccess("IOC added to blacklist.");
    } else if (result.duplicate) {
      showWarning("IOC is already blacklisted.");
    } else {
      showError("Failed to add IOC to blacklist.");
    }
  };

  const handleDeleteWord = async (entryId) => {
    const result = await removeFromBlacklist(entryId, "word");
    if (result.success) {
      showSuccess("Word removed from blacklist.");
    } else {
      showError("Failed to remove word from blacklist.");
    }
  };

  const handleDeleteIoc = async (entryId) => {
    const result = await removeFromBlacklist(entryId, "ioc");
    if (result.success) {
      showSuccess("IOC removed from blacklist.");
    } else {
      showError("Failed to remove IOC from blacklist.");
    }
  };

  return (
    <>
      <Card sx={{ p: 2, boxShadow: theme.shadows[1], borderRadius: 1 }}>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>Trends Blacklist Settings</Typography>
          <Typography variant="body1" sx={{ mb: 3 }}>
            Manage blacklisted words and IOC values that are excluded from the trends analytics charts.
          </Typography>
        </Box>

        <BlacklistSection
          title="Blacklisted Words"
          description="Words added here will be excluded from the Top Words in Headlines chart."
          entries={wordBlacklist}
          newValue={newWord}
          onNewValueChange={setNewWord}
          onAdd={handleAddWord}
          onDelete={handleDeleteWord}
          loading={loading}
        />

        <Divider sx={{ my: 3 }} />

        <BlacklistSection
          title="Blacklisted IOCs"
          description="IOC values added here will be excluded from the Top Indicators of Compromise chart."
          entries={iocBlacklist}
          newValue={newIoc}
          onNewValueChange={setNewIoc}
          onAdd={handleAddIoc}
          onDelete={handleDeleteIoc}
          loading={loading}
        />
      </Card>

      <NotificationSnackbar
        open={notification.open}
        message={notification.message}
        severity={notification.severity}
        onClose={hideNotification}
      />
    </>
  );
}
