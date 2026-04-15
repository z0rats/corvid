import React, { forwardRef } from "react";

import Button from '@mui/material/Button';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import { styled } from "@mui/system";
import SearchIcon from "@mui/icons-material/Search";

const CustomTextField = styled(TextField)({
  "& .MuiOutlinedInput-root": {
    borderRadius: 6,
    border: "none",
    "& fieldset": {
      border: "none",
    },
    "&:hover fieldset": {
      border: "none",
    },
    "&.Mui-focused fieldset": {
      border: "none",
    },
  },
});

const SearchButton = styled(Button)(({ theme }) => ({
  marginLeft: theme.spacing(1.25),
  borderRadius: 4,
  boxShadow: "none",
  "&:hover": {
    boxShadow: "none",
  },
}));

const SearchBar = forwardRef(
  (
    {
      value,
      placeholder = "Enter something...",
      onChange,
      onKeyDown,
      onSearchClick,
      buttonLabel = "Search",
    },
    ref
  ) => {
    return (
      <CustomTextField
        fullWidth
        variant="outlined"
        value={value}
        placeholder={placeholder}
        onChange={onChange}
        onKeyDown={onKeyDown}
        inputRef={ref}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <SearchButton
                  variant="contained"
                  color="primary"
                  startIcon={<SearchIcon />}
                  onClick={onSearchClick}
                >
                  {buttonLabel}
                </SearchButton>
              </InputAdornment>
            ),
          },
        }}
      />
    );
  }
);

SearchBar.displayName = 'SearchBar';

export default SearchBar;
