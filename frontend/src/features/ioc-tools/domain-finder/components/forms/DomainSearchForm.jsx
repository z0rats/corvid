import React, { useState } from 'react';
import { domainUtils } from '../../utils/domainUtils';
import SearchBar from '../../../../../core/components/ui/SearchBar';

export default function DomainSearchForm({ onSearch, onError }) {
  const [domainValue, setDomainValue] = useState('');

  const handleSearch = () => {
    const inputValue = domainValue.trim();
    
    if (!domainUtils.validateDomainPattern(inputValue)) {
      onError('Please enter a domain pattern to search for');
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
      placeholder="Please enter a domain pattern to search for..."
      buttonLabel="Search"
      onKeyDown={handleKeypress}
      onSearchClick={handleSearch}
    />
  );
}
