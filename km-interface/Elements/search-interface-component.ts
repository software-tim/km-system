import React, { useState, useEffect } from 'react';
import { Search, FileText, Clock, Star, Filter } from 'lucide-react';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  classification: string;
  relevance_score: number;
  created_at: string;
  file_type: string;
}

interface SearchResponse {
  status: string;
  results: SearchResult[];
  total: number;
  query: string;
  processing_time: number;
}

const SearchInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTime, setSearchTime] = useState<number | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedType, setSelectedType] = useState('all');

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('km-recent-searches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  const saveRecentSearch = (searchQuery: string) => {
    const updated = [searchQuery, ...recentSearches.filter(s => s !== searchQuery)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('km-recent-searches', JSON.stringify(updated));
  };

  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('https://km-orchestrator.azurewebsites.net/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          limit: 10
        }),
      });

      const data: SearchResponse = await response.json();
      
      if (data.status === 'success') {
        setResults(data.results || []);
        setTotalResults(data.total || 0);
        setSearchTime(data.processing_time || 0);
        saveRecentSearch(searchQuery);
      } else {
        setResults([]);
        setTotalResults(0);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  const handleQuickSearch = (quickQuery: string) => {
    setQuery(quickQuery);
    performSearch(quickQuery);
  };

  const highlightText = (text: string, searchQuery: string) => {
    if (!searchQuery) return text;
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200 text-yellow-900 px-1 rounded">$1</mark>');
  };

  const getFileTypeIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      case 'txt':
        return '📃';
      case 'md':
        return '📋';
      default:
        return '📄';
    }
  };

  const quickSearchTerms = [
    'artificial intelligence', 'machine learning', 'data analysis',
    'knowledge management', 'API documentation', 'system architecture'
  ];

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across all knowledge bases..."
            className="w-full pl-10 pr-20 py-3 bg-slate-800 border border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-white placeholder-slate-400"
          />
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex space-x-2">
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors"
            >
              <Filter className="w-4 h-4" />
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-md font-medium transition-colors"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </form>

      {/* Filters */}
      {showFilters && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
          <div className="flex flex-wrap gap-2">
            <label className="text-sm text-slate-300">Filter by type:</label>
            {['all', 'pdf', 'doc', 'txt', 'md'].map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  selectedType === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {type === 'all' ? 'All Types' : type.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Quick Search Terms */}
      {!query && recentSearches.length === 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-300">Quick Search:</h3>
          <div className="flex flex-wrap gap-2">
            {quickSearchTerms.map((term) => (
              <button
                key={term}
                onClick={() => handleQuickSearch(term)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-full border border-slate-600 transition-colors"
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Recent Searches */}
      {!query && recentSearches.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-300 flex items-center">
            <Clock className="w-4 h-4 mr-2" />
            Recent Searches:
          </h3>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((term, index) => (
              <button
                key={index}
                onClick={() => handleQuickSearch(term)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-full border border-slate-600 transition-colors"
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          {/* Results Header */}
          <div className="flex justify-between items-center">
            <div className="text-sm text-slate-400">
              Found {totalResults} results {searchTime && `in ${searchTime.toFixed(2)}ms`}
            </div>
            <div className="flex items-center space-x-2 text-sm text-slate-400">
              <Star className="w-4 h-4" />
              <span>Sorted by relevance</span>
            </div>
          </div>

          {/* Results List */}
          <div className="space-y-3">
            {results
              .filter(result => selectedType === 'all' || result.file_type === selectedType)
              .map((result) => (
              <div
                key={result.id}
                className="bg-slate-800 rounded-lg p-4 border border-slate-600 hover:border-slate-500 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getFileTypeIcon(result.file_type)}</span>
                    <h3 className="font-medium text-white">
                      <span dangerouslySetInnerHTML={{ 
                        __html: highlightText(result.title, query) 
                      }} />
                    </h3>
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-slate-400">
                    <span className="bg-slate-700 px-2 py-1 rounded">
                      {result.classification}
                    </span>
                    <span className="flex items-center">
                      <Star className="w-3 h-3 mr-1 text-yellow-500" />
                      {(result.relevance_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                
                <p className="text-slate-300 text-sm mb-2 line-clamp-2">
                  <span dangerouslySetInnerHTML={{ 
                    __html: highlightText(result.content.substring(0, 200) + '...', query) 
                  }} />
                </p>
                
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>
                    {new Date(result.created_at).toLocaleDateString()}
                  </span>
                  <button className="flex items-center space-x-1 hover:text-blue-400 transition-colors">
                    <FileText className="w-3 h-3" />
                    <span>View Document</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-slate-400">Searching knowledge base...</span>
        </div>
      )}

      {/* No Results */}
      {query && !loading && results.length === 0 && (
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-slate-300 mb-2">No results found</h3>
          <p className="text-slate-400">
            Try different keywords or check your spelling
          </p>
        </div>
      )}
    </div>
  );
};

export default SearchInterface;