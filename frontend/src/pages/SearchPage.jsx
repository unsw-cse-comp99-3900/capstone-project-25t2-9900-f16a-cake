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
    // 1. 搜索框状态
    const [query, setQuery] = useState('');
    // 2. 搜索结果状态（模拟数据，包含年份信息）
    const [searchResult, setSearchResult] = useState([]);
    // 3. 过滤器状态 - 支持年份和月份级联过滤
    const [yearFilter, setYearFilter] = useState('');
    const [monthFilter, setMonthFilter] = useState('');
    const [filteredResults, setFilteredResults] = useState([]);

    // 日期格式化函数：将日期格式化为 DD/MM/YYYY
    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0'); // getMonth() 返回 0-11
            const year = date.getFullYear();
            return `${day}/${month}/${year}`;
        } catch (error) {
            console.error('Date formatting error:', error);
            return 'Invalid Date';
        }
    };

    // ——————————————————————————————
    // 4. 点击 Search 时，将 query 作为唯一结果或清空
    const handleSearch = async () => {
        if (!query) {
            setSearchResult([]);
            setFilteredResults([]);
            setYearFilter('');
            setMonthFilter('');
            return;
        }
        try {
            // 调用 Flask 后端
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Search response:', data); // 调试日志
            
            // 直接保存对象数组
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

    // 5. 应用级联过滤器
    const applyFilter = () => {
        console.log('Apply filter clicked. Year:', yearFilter, 'Month:', monthFilter); // 调试信息
        
        // 如果没有任何过滤条件，显示所有搜索结果
        if (!yearFilter && !monthFilter) {
            console.log('No filters active, showing all results');
            setFilteredResults(searchResult);
            return;
        }
        
        let filtered = [...searchResult];
        
        // 第一步：按年份过滤
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
        
        // 第二步：在年份过滤结果基础上按月份过滤
        if (monthFilter) {
            filtered = filtered.filter(item => {
                if (item.document_date) {
                    try {
                        const itemMonth = new Date(item.document_date).getMonth() + 1; // getMonth() 返回 0-11
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

    // 6. 清除所有过滤器
    const clearAllFilters = () => {
        setYearFilter('');
        setMonthFilter('');
        setFilteredResults(searchResult);
    };
    
    // 7. 清除年份过滤器
    const clearYearFilter = () => {
        setYearFilter('');
        // 重新应用剩余的过滤器
        applyFilterWithValues('', monthFilter);
    };
    
    // 8. 清除月份过滤器  
    const clearMonthFilter = () => {
        setMonthFilter('');
        // 重新应用剩余的过滤器
        applyFilterWithValues(yearFilter, '');
    };
    
    // 9. 用指定值应用过滤器（避免状态更新延迟）
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

    // 当年份或月份过滤器变化时自动应用过滤器
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
            {/* ———— 第一块：搜索栏 ———— */}
            <Box
                sx={{
                    display: 'flex',          // Flex 容器
                    alignItems: 'flex-end',   // 子元素底部对齐
                    justifyContent: 'center', // 子元素水平居中
                    mt: 15                    // 距离顶部 15
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

            {/* ———— 第二块 & 第三块：并排布局容器 ———— */}
            <Box
                sx={{
                    display: 'flex',               
                    justifyContent: 'space-between', 
                    alignItems: 'flex-start',      
                    mt: 4,                         
                    px: 4                          
                }}
            >
                {/* —— 左侧过滤器 —— */}
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
                    {/* 英文标题 */}
                    <Typography variant="h6" sx={{ mb: 3, textAlign: 'center' }}>
                        Filters
                    </Typography>

                    {/* 年份过滤器 */}
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

                    {/* 月份过滤器 */}
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

                    {/* 操作按钮（英文） */}
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

                    {/* 过滤结果统计（英文） */}
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

                    {/* 说明文字（英文） */}
                    <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', mt: 2, color: 'text.secondary' }}>
                        Cascade filtering: Apply year filter first, then optionally add month filter
                    </Typography>
                </Paper>

                {/* —— 右侧结果 —— */}
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
                        // 确定要显示的结果：如果设置了任何过滤器，显示过滤结果；否则显示搜索结果
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
