import React, { useState } from "react";

import AccessTime from '@mui/icons-material/AccessTime';
import ChatBubbleOutline from '@mui/icons-material/ChatBubbleOutline';
import Forum from '@mui/icons-material/Forum';
import OpenInNew from '@mui/icons-material/OpenInNew';
import Person from '@mui/icons-material/Person';
import RedditIcon from '@mui/icons-material/Reddit';
import ThumbUp from '@mui/icons-material/ThumbUp';

import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid2";
import IconButton from "@mui/material/IconButton";
import Pagination from "@mui/material/Pagination";
import Stack from "@mui/material/Stack";
import Typography from '@mui/material/Typography';

import NoDetails from "../NoDetails";

const POSTS_PER_PAGE = 5;

const formatDate = (timestamp) => {
  if (!timestamp) return "N/A";
  return new Date(timestamp * 1000).toLocaleDateString();
};

const getTruncatedMessage = (message, maxLength = 200) => {
  if (!message) return "";
  return message.length > maxLength ? message.slice(0, maxLength) + "..." : message;
};

function PostCard({ post, index, isExpanded, onToggleExpand }) {
  return (
    <Card
      sx={{ mb: 1.5, p: 2, borderRadius: 1, boxShadow: 0 }}
    >
      <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
          <Typography variant="subtitle2" component="h2" sx={{ wordBreak: 'break-word', lineHeight: 1.4 }}>
            {post.title || "No Title"}
          </Typography>
          <IconButton
            size="small"
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            title="Open on Reddit"
            sx={{ flexShrink: 0 }}
          >
            <OpenInNew fontSize="small" />
          </IconButton>
        </Stack>

        <Stack
          direction="row"
          alignItems="center"
          spacing={1.5}
          sx={{ mt: 0.75, flexWrap: 'wrap', gap: 0.5 }}
        >
          {post.subreddit && (
            <Chip
              icon={<Forum sx={{ fontSize: 14 }} />}
              label={post.subreddit}
              size="small"
              variant="outlined"
              component="a"
              href={`https://www.reddit.com/${post.subreddit.startsWith('r/') ? post.subreddit : `r/${post.subreddit}`}`}
              target="_blank"
              rel="noopener noreferrer"
              clickable
            />
          )}
          <Typography variant="caption" color="text.secondary" sx={{ display: "flex", alignItems: "center" }}>
            <Person sx={{ fontSize: 14, mr: 0.5 }} /> {post.author || "N/A"}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: "flex", alignItems: "center" }}>
            <ThumbUp sx={{ fontSize: 14, mr: 0.5 }} /> {post.score ?? 0}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: "flex", alignItems: "center" }}>
            <ChatBubbleOutline sx={{ fontSize: 14, mr: 0.5 }} /> {post.num_comments ?? 0}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: "flex", alignItems: "center" }}>
            <AccessTime sx={{ fontSize: 14, mr: 0.5 }} /> {formatDate(post.created_utc)}
          </Typography>
        </Stack>

        {post.message && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {isExpanded ? post.message : getTruncatedMessage(post.message, 200)}
            </Typography>
            {post.message.length > 200 && (
              <Button
                onClick={() => onToggleExpand(index)}
                size="small"
                sx={{ mt: 0.5, p: 0, textTransform: 'none', minWidth: 'auto' }}
              >
                {isExpanded ? "Read less" : "Read more"}
              </Button>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default function RedditDetails({ result, ioc }) {
  const [expandedIndices, setExpandedIndices] = useState(new Set());
  const [page, setPage] = useState(1);

  const toggleExpanded = (index) => {
    setExpandedIndices(prev => {
      const next = new Set(prev);
      next.has(index) ? next.delete(index) : next.add(index);
      return next;
    });
  };

  if (!result) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message="Loading Reddit mentions..." />
      </Box>
    );
  }

  if (result.error) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={`Error fetching Reddit mentions: ${result.message || result.error}`} />
      </Box>
    );
  }

  const posts = result?.posts;

  if (!Array.isArray(posts) || posts.length === 0) {
    return (
      <Box sx={{ margin: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
        <NoDetails message={`No Reddit mentions found for "${ioc}".`} />
      </Box>
    );
  }

  const totalPages = Math.ceil(posts.length / POSTS_PER_PAGE);
  const paginatedPosts = posts.slice((page - 1) * POSTS_PER_PAGE, page * POSTS_PER_PAGE);

  return (
    <Box sx={{ margin: 1, mt: 0 }}>
      <Grid container spacing={1} alignItems="center" mb={1.5}>
        <RedditIcon color="action" />
        <Typography variant="h6" component="div" sx={{ ml: 1 }}>
          Reddit Mentions ({posts.length})
        </Typography>
      </Grid>

      {paginatedPosts.map((post, index) => {
        const globalIndex = (page - 1) * POSTS_PER_PAGE + index;
        return (
          <PostCard
            key={post.id || globalIndex}
            post={post}
            index={globalIndex}
            isExpanded={expandedIndices.has(globalIndex)}
            onToggleExpand={toggleExpanded}
          />
        );
      })}

      {totalPages > 1 && (
        <Stack alignItems="center" sx={{ mt: 1 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_, value) => setPage(value)}
            size="small"
            color="primary"
          />
        </Stack>
      )}
    </Box>
  );
}
