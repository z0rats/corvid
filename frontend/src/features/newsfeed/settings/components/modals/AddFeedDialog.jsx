import React, { useState, useMemo, useEffect, useCallback } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useDropzone } from "react-dropzone";

const INITIAL_FEED = { name: "", url: "" };

export default function AddFeedDialog({ open, onClose, onSubmit, processIconFile }) {
  const [newFeed, setNewFeed] = useState(INITIAL_FEED);
  const [iconFile, setIconFile] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const iconPreviewUrl = useMemo(() => {
    return iconFile ? URL.createObjectURL(iconFile) : null;
  }, [iconFile]);

  useEffect(() => {
    return () => {
      if (iconPreviewUrl) URL.revokeObjectURL(iconPreviewUrl);
    };
  }, [iconPreviewUrl]);

  const resetForm = useCallback(() => {
    setNewFeed(INITIAL_FEED);
    setIconFile(null);
    setErrorMessage("");
    setLoading(false);
  }, []);

  const handleClose = useCallback(() => {
    resetForm();
    onClose();
  }, [resetForm, onClose]);

  const handleIconDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;
    const processed = await processIconFile(file);
    setIconFile(processed);
  }, [processIconFile]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop: handleIconDrop,
    accept: {
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/gif": [".gif"],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
  });

  const handleSubmit = async () => {
    if (!newFeed.name || !newFeed.url) {
      setErrorMessage("Please provide both feed name and URL");
      return;
    }

    setLoading(true);
    const result = await onSubmit({ name: newFeed.name, url: newFeed.url, iconFile });

    if (result.success) {
      handleClose();
    } else {
      const detail = result.error?.response?.data?.detail || "Error adding feed";
      setErrorMessage(detail);
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add New Feed</DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
          <Box
            {...getRootProps()}
            sx={{
              width: 80,
              height: 80,
              border: "2px dashed",
              borderColor: "divider",
              borderRadius: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              backgroundColor: "background.paper",
              "&:hover": { borderColor: "primary.main", backgroundColor: "action.hover" },
              overflow: "hidden",
            }}
          >
            <input {...getInputProps()} />
            {iconPreviewUrl ? (
              <Box
                component="img"
                src={iconPreviewUrl}
                alt="Icon preview"
                sx={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : (
              <Typography variant="caption" color="text.secondary" textAlign="center">
                Drop icon
              </Typography>
            )}
          </Box>
        </Box>
        <Typography variant="caption" color="text.secondary" display="block" textAlign="center" sx={{ mb: 2 }}>
          Optional — a favicon will be fetched automatically
        </Typography>

        <TextField
          label="Feed Name"
          value={newFeed.name}
          onChange={(e) => { setNewFeed({ ...newFeed, name: e.target.value }); setErrorMessage(""); }}
          variant="outlined"
          size="small"
          fullWidth
          disabled={loading}
          sx={{ mb: 2 }}
        />
        <TextField
          label="Feed URL"
          value={newFeed.url}
          onChange={(e) => { setNewFeed({ ...newFeed, url: e.target.value }); setErrorMessage(""); }}
          variant="outlined"
          size="small"
          fullWidth
          disabled={loading}
        />

        {errorMessage && (
          <Alert severity="error" sx={{ mt: 2 }}>{errorMessage}</Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} variant="outlined" disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!newFeed.name || !newFeed.url || loading}
          startIcon={loading ? <CircularProgress size={16} /> : null}
        >
          Add Feed
        </Button>
      </DialogActions>
    </Dialog>
  );
}
