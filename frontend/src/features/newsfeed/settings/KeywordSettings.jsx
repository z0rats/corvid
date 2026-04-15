import React, { useState } from "react";
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useTheme } from "@mui/material/styles";
import AddIcon from "@mui/icons-material/Add";

import { useKeywordSettings } from "../hooks/api/useKeywordSettingsApi";
import { useNotification } from "../../../core/hooks/ui/useNotification";
import NotificationSnackbar from "../components/ui/NotificationSnackbar";

export default function KeywordSettings() {
  const theme = useTheme();
  const [newKeyword, setNewKeyword] = useState("");

  const {
    keywords,
    keywordMatchingEnabled,
    loading,
    toggleKeywordMatching,
    addKeyword,
    deleteKeyword,
  } = useKeywordSettings();

  const { notification, showSuccess, showError, showWarning, hideNotification } = useNotification();

  const handleToggle = async (event) => {
    const result = await toggleKeywordMatching(event.target.checked);
    if (result.success) {
      showSuccess("Keyword matching setting updated.");
    } else {
      showError("Failed to update keyword matching setting.");
    }
  };

  const handleAdd = async () => {
    if (newKeyword.trim() === "") return;

    const result = await addKeyword(newKeyword);
    if (result.success) {
      setNewKeyword("");
      showSuccess("Keyword added successfully.");
    } else if (result.duplicate) {
      showWarning("Keyword already exists.");
    } else {
      showError("Failed to add keyword.");
    }
  };

  const handleDelete = async (keywordId) => {
    const result = await deleteKeyword(keywordId);
    if (result.success) {
      showSuccess("Keyword deleted successfully.");
    } else {
      showError("Failed to delete keyword.");
    }
  };

  return (
    <>
      <Card sx={{ p: 2, boxShadow: theme.shadows[1], borderRadius: 1 }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            Keyword Matching Settings
          </Typography>
          <Typography variant="body1" sx={{ mb: 3 }}>
            Enable keyword matching to highlight news articles containing specific keywords of interest.
          </Typography>
        </Box>

        <FormControlLabel
          control={<Switch checked={keywordMatchingEnabled} onChange={handleToggle} color="primary" sx={{ mr: 1 }} />}
          label="Enable Keyword Matching"
          sx={{ mb: 2 }}
        />

        {keywordMatchingEnabled && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6">Manage Keywords</Typography>
            <Box sx={{ display: "flex", alignItems: "center", mt: 2, flexWrap: "wrap" }}>
              <TextField
                label="Add New Keyword"
                value={newKeyword}
                size="small"
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAdd();
                  }
                }}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={handleAdd} edge="end" color="primary" sx={{ mr: "-8px" }} aria-label="Add keyword">
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

            <Box sx={{ mt: 2 }}>
              {loading ? (
                <CircularProgress />
              ) : keywords.length > 0 ? (
                <Box sx={{ display: "flex", flexWrap: "wrap" }}>
                  {keywords.map((keyword) => (
                    <Chip key={keyword.id} label={keyword.keyword} onDelete={() => handleDelete(keyword.id)} sx={{ m: 0.5 }} />
                  ))}
                </Box>
              ) : (
                <Typography>No keywords added yet.</Typography>
              )}
            </Box>
          </Box>
        )}
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
