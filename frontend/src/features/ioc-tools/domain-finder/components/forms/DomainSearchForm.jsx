import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { domainUtils } from '../../utils/domainUtils';
import SearchBar from '../../../../../core/components/ui/SearchBar';

export default function DomainSearchForm({ onSearch, onError }) {
  const { t } = useTranslation('iocTools');
  const [domainValue, setDomainValue] = useState('');

  const handleSearch = () => {
    const inputValue = domainValue.trim();

    if (!domainUtils.validateDomainPattern(inputValue)) {
      onError(t('domainFinder.errors.invalidPattern'));
      return;
    }

    onError(null);
    onSearch(inputValue);
  };

  const handleKeypress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const handleChange = (event) => {
    setDomainValue(event.target.value);
  };

  return (
    <SearchBar
      value={domainValue}
      onChange={handleChange}
      placeholder={t('domainFinder.searchForm.placeholder')}
      buttonLabel={t('domainFinder.searchForm.buttonLabel')}
      onKeyDown={handleKeypress}
      onSearchClick={handleSearch}
    />
  );
}
