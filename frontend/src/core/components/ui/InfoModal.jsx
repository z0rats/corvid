import React from "react";
import Box from "@mui/material/Box";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import IconButton from "@mui/material/IconButton";
import Typography from "@mui/material/Typography";
import CloseIcon from "@mui/icons-material/Close";
import InfoIcon from "@mui/icons-material/Info";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { styled } from "@mui/material/styles";

const MarkdownContainer = styled(Box)(({ theme }) => ({
  overflowY: "auto",
  maxHeight: "60vh",
  padding: theme.spacing(2),
  "& table": {
    width: "100%",
    borderCollapse: "collapse",
    marginTop: theme.spacing(2),
    "& th, & td": {
      border: `1px solid ${theme.palette.divider}`,
      padding: theme.spacing(1),
      textAlign: "left",
    },
    "& th": {
      backgroundColor: theme.palette.grey[200],
    },
  },
  "& p": {
    marginBottom: theme.spacing(2),
  },
  "& h4": {
    marginBottom: theme.spacing(2),
  },
}));

export default function InfoModal({ open, onClose, title, text }) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="h5" component="span" sx={{ display: "flex", alignItems: "center" }}>
          <InfoIcon sx={{ mr: 1 }} /> {title}
        </Typography>
        <IconButton onClick={onClose} aria-label="Close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <MarkdownContainer>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
        </MarkdownContainer>
      </DialogContent>
    </Dialog>
  );
}
