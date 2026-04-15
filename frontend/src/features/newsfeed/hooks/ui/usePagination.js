import { PAGINATION } from '../../constants/newsfeedConstants';

const scrollToTop = () => {
  window.scrollTo({ top: 120, behavior: "smooth" });
};

const getTotalPages = (totalCount) => {
  return Math.ceil(totalCount / PAGINATION.DEFAULT_PAGE_SIZE);
};

export function usePagination(page, setPage) {
  const handlePageChange = (event, value) => {
    setPage(value);
    scrollToTop();
  };

  return {
    handlePageChange,
    scrollToTop,
    getTotalPages,
  };
}
