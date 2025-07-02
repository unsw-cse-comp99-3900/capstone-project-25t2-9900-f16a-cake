import React, { useState } from 'react';
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
    // 3. 过滤器状态
    const [filterType, setFilterType] = useState('');
    const [filterValue, setFilterValue] = useState('');
    const [filteredResults, setFilteredResults] = useState([]);

    // ——————————————————————————————
    // 4. 点击 Search 时，将 query 作为唯一结果或清空
    const handleSearch = async () => {
        if (!query) {
            setSearchResult([]);
            setFilteredResults([]);
            setFilterType('');
            setFilterValue('');
            return;
        }
        // 调用 Flask 后端
        const response = await fetch('http://127.0.0.1:8000/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });
        const data = await response.json();
        // 假设返回格式为 { results: [{title, url, score}, ...] }
        const results = data.results.map(
            r => `${r.title} - ${r.url} (Score: ${r.score.toFixed(2)}) - ${r.year}`
        );
        setSearchResult(results);
        setFilteredResults(results);
        setFilterType('');
        setFilterValue('');
    };

    // 5. 应用过滤器
    const applyFilter = () => {
        if (!filterType || !filterValue) {
            setFilteredResults(searchResult);
            return;
        }

        const filtered = searchResult.filter(item => {
            switch (filterType) {
                case 'year':
                    // 检查搜索结果是否以指定年份结尾
                    return item.endsWith(` - ${filterValue}`);
                default:
                    return true;
            }
        });

        setFilteredResults(filtered);
    };

    // 6. 清除过滤器
    const clearFilter = () => {
        setFilterType('');
        setFilterValue('');
        setFilteredResults(searchResult);
    };

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
                        Filter
                    </Typography>

                    {/* 过滤类型选择（英文） */}
                    <FormControl fullWidth sx={{ mb: 2 }}>
                        <InputLabel>Filter Type</InputLabel>
                        <Select
                            value={filterType}
                            label="Filter Type"
                            onChange={(e) => setFilterType(e.target.value)}
                        >
                            <MenuItem value="year">Year</MenuItem>
                        </Select>
                    </FormControl>

                    {/* 过滤值输入（英文提示） */}
                    <TextField
                        label={filterType === 'year' ? 'Year' : 'Filter Value'}
                        variant="outlined"
                        type={filterType === 'year' ? 'number' : 'text'}
                        value={filterValue}
                        onChange={(e) => setFilterValue(e.target.value)}
                        placeholder={filterType === 'year' ? 'e.g. 2023' : 'Enter filter value'}
                        fullWidth
                        sx={{ mb: 2 }}
                    />

                    {/* 操作按钮（英文） */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Button
                            variant="contained"
                            onClick={applyFilter}
                            sx={{ flex: 1 }}
                        >
                            Apply Filter
                        </Button>
                        <Button
                            variant="outlined"
                            onClick={clearFilter}
                            sx={{ flex: 1 }}
                        >
                            Clear Filter
                        </Button>
                    </Box>

                    {/* 过滤结果统计（英文） */}
                    <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary' }}>
                        Displaying {filteredResults.length || searchResult.length} of {searchResult.length} results
                    </Typography>

                    {/* 说明文字（英文） */}
                    <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', mt: 2, color: 'text.secondary' }}>
                        Currently supports: Year filter
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
                    {(filteredResults.length > 0 || searchResult.length > 0) ? (
                        <List>
                            {(filteredResults.length > 0 ? filteredResults : searchResult).map((item, idx) => (
                                <ListItem key={idx}>
                                    <ListItemText primary={item} />
                                </ListItem>
                            ))}
                        </List>
                    ) : (
                        <Typography
                            variant="body1"
                            sx={{ textAlign: 'center', wordBreak: 'break-all' }}
                        >
                            no search content
                        </Typography>
                    )}
                </Paper>
            </Box>
        </>
    );
}
