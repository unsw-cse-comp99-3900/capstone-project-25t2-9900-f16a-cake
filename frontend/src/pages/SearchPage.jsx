import React, { useState, useEffect } from 'react';
import {
    Box,
    TextField,
    Button,
    Paper,
    Typography,
    List,
    ListItem,
    ListItemText,
    FormControl,
    InputLabel,
    Select,
    MenuItem
} from '@mui/material';

export default function SearchPage() {
    // ——————————————————————————————
    // 1. Search input state
    const [query, setQuery] = useState('');
    // 2. Search results state (mock data, includes year information)
    const [searchResult, setSearchResult] = useState([]);
    // 3. Filter state - supports year and month cascading filters
    const [yearFilter, setYearFilter] = useState('');
    const [monthFilter, setMonthFilter] = useState('');
    const [filteredResults, setFilteredResults] = useState([]);

    // Date formatting function: formats date to DD/MM/YYYY
    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0'); // getMonth() returns 0-11
            const year = date.getFullYear();
            return `${day}/${month}/${year}`;
        } catch (error) {
            console.error('Date formatting error:', error);
            return 'Invalid Date';
        }
    };


    // 4. When Search is clicked, set query as unique result or clear
    const handleSearch = async () => {
        if (!query) {
            setSearchResult([]);
            setFilteredResults([]);
            setYearFilter('');
            setMonthFilter('');
            return;
        }
        try {
            // Call Flask backend
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Search response:', data); // Debug log
            
            // Save object array directly
            setSearchResult(data.results || []);
            setFilteredResults(data.results || []);
            setYearFilter('');
            setMonthFilter('');
        } catch (error) {
            console.error('Search error:', error);
            setSearchResult([]);
            setFilteredResults([]);
        }
    };

    // 5. Apply cascading filters
    const applyFilter = () => {
        console.log('Apply filter clicked. Year:', yearFilter, 'Month:', monthFilter); // Debug info
        
        // If no filter conditions, show all search results
        if (!yearFilter && !monthFilter) {
            console.log('No filters active, showing all results');
            setFilteredResults(searchResult);
            return;
        }
        
        let filtered = [...searchResult];
        
        // Step 1: Filter by year
        if (yearFilter) {
            filtered = filtered.filter(item => {
                if (item.document_date) {
                    try {
                        const itemYear = new Date(item.document_date).getFullYear();
                        const match = String(itemYear) === String(yearFilter);
                        console.log('Year filter:', item.title, 'year:', itemYear, 'match:', match);
                        return match;
                    } catch (error) {
                        console.error('Date parsing error for:', item.document_date);
                        return false;
                    }
                }
                return false;
            });
            console.log('After year filter:', filtered.length, 'results');
        }
        
        // Step 2: Filter by month based on year filter results
        if (monthFilter) {
            filtered = filtered.filter(item => {
                if (item.document_date) {
                    try {
                        const itemMonth = new Date(item.document_date).getMonth() + 1; // getMonth() returns 0-11
                        const match = String(itemMonth) === String(monthFilter);
                        console.log('Month filter:', item.title, 'month:', itemMonth, 'match:', match);
                        return match;
                    } catch (error) {
                        console.error('Date parsing error for:', item.document_date);
                        return false;
                    }
                }
                return false;
            });
            console.log('After month filter:', filtered.length, 'results');
        }
        
        console.log('Final filtered results:', filtered.length, 'out of', searchResult.length);
        setFilteredResults(filtered);
    };

    // 6. Clear all filters
    const clearAllFilters = () => {
        setYearFilter('');
        setMonthFilter('');
        setFilteredResults(searchResult);
    };
    
    // 7. Clear year filter
    const clearYearFilter = () => {
        setYearFilter('');
        // Reapply remaining filters
        applyFilterWithValues('', monthFilter);
    };
    
    // 8. Clear month filter  
    const clearMonthFilter = () => {
        setMonthFilter('');
        // Reapply remaining filters
        applyFilterWithValues(yearFilter, '');
    };
    
    // 9. Apply filters with specified values (avoid state update delay)
    const applyFilterWithValues = (year, month) => {
        if (!year && !month) {
            setFilteredResults(searchResult);
            return;
        }
        
        let filtered = [...searchResult];
        
        if (year) {
            filtered = filtered.filter(item => {
                if (item.document_date) {
                    try {
                        const itemYear = new Date(item.document_date).getFullYear();
                        return String(itemYear) === String(year);
                    } catch (error) {
                        return false;
                    }
                }
                return false;
            });
        }
        
        if (month) {
            filtered = filtered.filter(item => {
                if (item.document_date) {
                    try {
                        const itemMonth = new Date(item.document_date).getMonth() + 1;
                        return String(itemMonth) === String(month);
                    } catch (error) {
                        return false;
                    }
                }
                return false;
            });
        }
        
        setFilteredResults(filtered);
    };

    // Automatically apply filters when year or month filter changes
    useEffect(() => {
        if (searchResult.length > 0) {
            applyFilterWithValues(yearFilter, monthFilter);
        }
    }, [yearFilter, monthFilter, searchResult]);

    useEffect(() => {
        document.title = "Search";
    }, []);

    return (
        <>
            {/* ———— First Block: Search Bar ———— */}
            <Box
                sx={{
                    display: 'flex',          // Flex container
                    alignItems: 'flex-end',   // Align child elements to bottom
                    justifyContent: 'center', // Center child elements horizontally
                    mt: 15                    // Distance from top 15
                }}
            >
                <TextField
                    label="Search Content"
                    variant="outlined"
                    value={query}                         
                    onChange={e => setQuery(e.target.value)} 
                    sx={{ minWidth: 600 }}                
                />
                <Button
                    variant="contained"
                    onClick={handleSearch}               
                    sx={{ ml: 2, height: '56px' }}       
                >
                    Search
                </Button>
            </Box>

            {/* ———— Second & Third Block: Side-by-side Layout Container ———— */}
            <Box
                sx={{
                    display: 'flex',               
                    justifyContent: 'space-between', 
                    alignItems: 'flex-start',      
                    mt: 4,                         
                    px: 4                          
                }}
            >
                {/* —— Left Side Filters —— */}
                <Paper
                    elevation={3}
                    sx={{
                        width: 375,                  
                        height: 400,                 
                        p: 3,                        
                        overflow: 'auto',            
                        backgroundColor: '#f5f5f5'   
                    }}
                >
                    {/* English Title */}
                    <Typography variant="h6" sx={{ mb: 3, textAlign: 'center' }}>
                        Filters
                    </Typography>

                    {/* Year Filter */}
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
                            Year Filter
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <TextField
                                label="Year"
                                variant="outlined"
                                type="number"
                                value={yearFilter}
                                onChange={(e) => setYearFilter(e.target.value)}
                                placeholder="e.g. 2025"
                                size="small"
                                sx={{ flex: 1 }}
                            />
                            <Button
                                variant="outlined"
                                size="small"
                                onClick={clearYearFilter}
                                disabled={!yearFilter}
                                sx={{ minWidth: 'auto', px: 1 }}
                            >
                                ✕
                            </Button>
                        </Box>
                    </Box>

                    {/* Month Filter */}
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
                            Month Filter
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <FormControl size="small" sx={{ flex: 1 }}>
                                <InputLabel>Month</InputLabel>
                                <Select
                                    value={monthFilter}
                                    label="Month"
                                    onChange={(e) => setMonthFilter(e.target.value)}
                                >
                                    <MenuItem value="1">January</MenuItem>
                                    <MenuItem value="2">February</MenuItem>
                                    <MenuItem value="3">March</MenuItem>
                                    <MenuItem value="4">April</MenuItem>
                                    <MenuItem value="5">May</MenuItem>
                                    <MenuItem value="6">June</MenuItem>
                                    <MenuItem value="7">July</MenuItem>
                                    <MenuItem value="8">August</MenuItem>
                                    <MenuItem value="9">September</MenuItem>
                                    <MenuItem value="10">October</MenuItem>
                                    <MenuItem value="11">November</MenuItem>
                                    <MenuItem value="12">December</MenuItem>
                                </Select>
                            </FormControl>
                            <Button
                                variant="outlined"
                                size="small"
                                onClick={clearMonthFilter}
                                disabled={!monthFilter}
                                sx={{ minWidth: 'auto', px: 1 }}
                            >
                                ✕
                            </Button>
                        </Box>
                        <Typography variant="caption" sx={{ display: 'block', mt: 1, color: 'text.secondary' }}>
                            Apply year filter first, then month
                        </Typography>
                    </Box>

                    {/* Action Buttons (English) */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        {(yearFilter || monthFilter) && (
                            <Button
                                variant="outlined"
                                onClick={clearAllFilters}
                                sx={{ flex: 1 }}
                                color="secondary"
                            >
                                Clear All Filters
                            </Button>
                        )}
                        {!yearFilter && !monthFilter && (
                            <Typography 
                                variant="body2" 
                                sx={{ 
                                    textAlign: 'center', 
                                    color: 'text.secondary', 
                                    fontStyle: 'italic',
                                    py: 1,
                                    flex: 1
                                }}
                            >
                                Filters will apply automatically
                            </Typography>
                        )}
                    </Box>

                    {/* Filter Results Statistics (English) */}
                    <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary' }}>
                        {(() => {
                            const hasFilters = yearFilter || monthFilter;
                            const displayCount = hasFilters ? filteredResults.length : searchResult.length;
                            const totalCount = searchResult.length;
                            
                            let filterStatus = '';
                            if (hasFilters) {
                                const filters = [];
                                if (yearFilter) filters.push(`Year: ${yearFilter}`);
                                if (monthFilter) filters.push(`Month: ${monthFilter}`);
                                filterStatus = ` (${filters.join(', ')})`;
                            }
                            
                            return `Displaying ${displayCount} of ${totalCount} results${filterStatus}`;
                        })()}
                    </Typography>

                    {/* Description Text (English) */}
                    <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', mt: 2, color: 'text.secondary' }}>
                        Cascade filtering: Apply year filter first, then optionally add month filter
                    </Typography>
                </Paper>

                {/* —— Right Side Results —— */}
                <Paper
                    elevation={3}
                    sx={{
                        width: 750,                  
                        height: 400,                 
                        p: 3,                        
                        overflow: 'auto',
                        backgroundColor: '#f5f5f5',
                        mr: 57
                    }}
                >
                    {(() => {
                        // Determine results to display: if any filters are set, show filtered results; otherwise show search results
                        const displayResults = (yearFilter || monthFilter) ? filteredResults : searchResult;
                        
                        return displayResults.length > 0 ? (
                            <List>
                                {displayResults.map((item, idx) => (
                                <ListItem key={idx}>
                                    <ListItemText
                                        primary={
                                            <a
                                                href={`/pdfs/${item.pdf_path}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                style={{ textDecoration: 'underline', color: '#1976d2' }}
                                            >
                                                {item.title}
                                            </a>
                                        }
                                        secondary={`Date: ${formatDate(item.document_date)}`}
                                    />
                                </ListItem>
                                ))}
                            </List>
                        ) : (
                            <Typography
                                variant="body1"
                                sx={{ textAlign: 'center', wordBreak: 'break-all' }}
                            >
                                {(yearFilter || monthFilter) ? 'No matching results found' : 'no search content'}
                            </Typography>
                        );
                    })()}
                </Paper>
            </Box>
        </>
    );
}
