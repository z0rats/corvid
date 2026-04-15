import React from "react";
import Box from '@mui/material/Box';
import Pagination from '@mui/material/Pagination';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { useNewsfeedData } from "../hooks/api/useNewsfeedApi";
import { useArticleActions } from "../hooks/api/useArticleActions";
import { usePagination } from "../hooks/ui/usePagination";
import { TLP_COLORS, PAGINATION } from "../constants/newsfeedConstants";

import NewsArticleItem from "./NewsArticleItem";
import NewsfeedSkeleton from "./NewsfeedSkeleton";
import Filters from "./Filters";

export default function Feed() {
  const {
    result,
    loading,
    page,
    setPage,
    filters,
    setFilters,
    updateArticle,
    updateArticleField,
    applyFilters,
    resetFilters,
    refreshData,
  } = useNewsfeedData();

  const { handlePageChange, getTotalPages } = usePagination(page, setPage);

  const {
    analyzing,
    updatingTlp,
    handleAnalyze,
    handleTlpUpdate,
    handleNoteSave,
    handleNoteDelete,
  } = useArticleActions(updateArticle, updateArticleField);

  return (
    <Stack spacing={1} width="100%">
      <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2, width: "100%" }}>
        <Box sx={{ flex: 1, mb: 1 }}>
          <Filters
            filters={filters}
            setFilters={setFilters}
            applyFilters={applyFilters}
            resetFilters={resetFilters}
            refreshData={refreshData}
          />
        </Box>
      </Box>

      {loading ? (
        <NewsfeedSkeleton pageSize={PAGINATION.DEFAULT_PAGE_SIZE} />
      ) : result.articles && result.articles.length > 0 ? (
        <>
          <Stack spacing={2}>
            {result.articles.map((item) => (
              <NewsArticleItem
                key={item.id}
                item={item}
                updateArticle={updateArticle}
                updateArticleField={updateArticleField}
                tlpColors={TLP_COLORS}
                onAnalyze={handleAnalyze}
                onTlpUpdate={handleTlpUpdate}
                onNoteSave={handleNoteSave}
                onNoteDelete={handleNoteDelete}
                analyzing={analyzing[item.id]}
                updatingTlp={updatingTlp[item.id]}
              />
            ))}
          </Stack>

          <Pagination
            count={getTotalPages(result.total_count)}
            page={page}
            color="primary"
            shape="rounded"
            size="large"
            showFirstButton
            showLastButton
            onChange={handlePageChange}
            sx={{ display: "flex", justifyContent: "center", mt: 4 }}
          />
        </>
      ) : (
        <Typography variant="h6" align="center" sx={{ mt: 4 }}>
          No articles found.
        </Typography>
      )}
    </Stack>
  );
}
