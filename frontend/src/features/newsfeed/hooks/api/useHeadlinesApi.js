import { useState, useEffect, useCallback, useMemo } from 'react';
import { newsfeedApi } from '../../services/api/newsfeedApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('Headlines');

export function useHeadlines() {
  const [headlines, setHeadlines] = useState([]);
  const [timeFilter, setTimeFilter] = useState('2d');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [orderBy, setOrderBy] = useState('date');
  const [order, setOrder] = useState('desc');
  const [sourceFilter, setSourceFilter] = useState('');
  const [titleFilter, setTitleFilter] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let ignore = false;

    const fetchHeadlines = async () => {
      try {
        const data = await newsfeedApi.getRecentArticles(timeFilter);
        if (!ignore) {
          setHeadlines(data);
        }
      } catch (error) {
        if (!ignore) {
          logger.error('Error fetching headlines:', error);
        }
      }
    };

    fetchHeadlines();
    return () => { ignore = true; };
  }, [timeFilter, refreshKey]);

  const handleSort = useCallback((property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  }, [orderBy, order]);

  const handleChangePage = useCallback((event, newPage) => {
    setPage(newPage);
  }, []);

  const handleChangeRowsPerPage = useCallback((event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshKey(prev => prev + 1);
  }, []);

  const filteredData = useMemo(() => {
    return headlines.filter(item => {
      const matchesSource = item.feedname.toLowerCase().includes(sourceFilter.toLowerCase());
      const matchesTitle = item.title.toLowerCase().includes(titleFilter.toLowerCase());
      return matchesSource && matchesTitle;
    });
  }, [headlines, sourceFilter, titleFilter]);

  const displayData = useMemo(() => {
    const sorted = [...filteredData].sort((a, b) => {
      if (orderBy === 'date') {
        return order === 'asc'
          ? new Date(a.date) - new Date(b.date)
          : new Date(b.date) - new Date(a.date);
      }
      if (order === 'asc') {
        return a[orderBy] > b[orderBy] ? 1 : -1;
      }
      return a[orderBy] < b[orderBy] ? 1 : -1;
    });
    return sorted.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [filteredData, orderBy, order, page, rowsPerPage]);

  const filteredCount = filteredData.length;

  return {
    headlines,
    timeFilter,
    setTimeFilter,
    page,
    rowsPerPage,
    orderBy,
    order,
    sourceFilter,
    setSourceFilter,
    titleFilter,
    setTitleFilter,
    handleSort,
    handleChangePage,
    handleChangeRowsPerPage,
    handleRefresh,
    displayData,
    filteredCount,
  };
}
