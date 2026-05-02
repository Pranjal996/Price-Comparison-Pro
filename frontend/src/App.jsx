import React, { useState } from 'react';
import axios from 'axios';
import { Search, Loader2, Image as ImageIcon, ExternalLink, TrendingDown, Frown, Zap } from 'lucide-react';
import './index.css';

const SITE_COLORS = {
  Amazon:   '#ff9900',
  Flipkart: '#2874f0',
  Meesho:   '#f43397',
  Ajio:     '#ee2222',
};

function App() {
  const [query, setQuery]         = useState('');
  const [results, setResults]     = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError]         = useState(null);
  const [sortBy, setSortBy]       = useState('price_asc');
  const [maxPrice, setMaxPrice]   = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setHasSearched(true);
    setError(null);
    setResults([]);

    try {
      const res = await axios.get(
        `http://localhost:5000/api/search?q=${encodeURIComponent(query)}`
      );
      setResults(res.data.results || []);
    } catch (err) {
      setError('Could not connect to the backend. Make sure python app.py is running.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // exclude unavailable from filter + best-deal logic
  const availableResults = results.filter(r => r.price_val < 999999999);
  const filteredResults  = availableResults.filter(r => !maxPrice || r.price_val <= Number(maxPrice));
  const unavailableResults = results.filter(r => r.price_val >= 999999999);

  const sortedAvailable = [...filteredResults].sort((a, b) => {
    if (sortBy === 'price_asc')  return a.price_val - b.price_val;
    if (sortBy === 'price_desc') return b.price_val - a.price_val;
    return 0;
  });

  const displayResults = [...sortedAvailable, ...unavailableResults];
  const bestDealPrice  = filteredResults.length > 0
    ? Math.min(...filteredResults.map(r => r.price_val))
    : Infinity;

  return (
    <div className="app-container">
      <header>
        <h1>Price Comparison Pro</h1>
        <p>Compare prices across Amazon, Flipkart, Ajio, Meesho &amp; Official Stores</p>
      </header>

      <form className="search-container" onSubmit={handleSearch}>
        <div className="search-input-wrapper">
          <Search size={20} />
          <input
            type="text"
            className="search-input"
            placeholder="Search any product (e.g. Samsung TV, Nike Shoes)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button type="submit" className="search-button" disabled={isLoading}>
          {isLoading ? <Loader2 className="spinner" size={20} /> : <><Zap size={18}/> Search Deals</>}
        </button>
      </form>

      {isLoading && (
        <div className="loading-container">
          <Loader2 className="spinner" size={52} />
          <p>Scanning Amazon, Flipkart, Ajio &amp; Meesho simultaneously…</p>
          <span className="loading-sub">This may take 10–15 seconds</span>
        </div>
      )}

      {error && !isLoading && (
        <div className="no-results" style={{ color: '#ef4444' }}>
          <Frown size={48} />
          <p>{error}</p>
        </div>
      )}

      {!isLoading && hasSearched && !error && results.length === 0 && (
        <div className="no-results">
          <Frown size={48} />
          <p>No results found for "<strong>{query}</strong>"</p>
        </div>
      )}

      {!isLoading && results.length > 0 && (
        <div className="results-container">
          <div className="results-header">
            <div>
              <h2>Found <span className="accent">{filteredResults.length}</span> result{filteredResults.length !== 1 ? 's' : ''}</h2>
              {bestDealPrice < Infinity && (
                <p className="savings-hint">
                  Best deal saves you up to ₹{(Math.max(...filteredResults.map(r=>r.price_val)) - bestDealPrice).toLocaleString('en-IN')} vs highest price
                </p>
              )}
            </div>
            <div className="filter-row">
              <input
                type="number"
                placeholder="Max Price (₹)"
                className="sort-select"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                style={{ width: '140px' }}
              />
              <select
                className="sort-select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="price_asc">Price: Low → High</option>
                <option value="price_desc">Price: High → Low</option>
              </select>
            </div>
          </div>

          <div className="products-grid">
            {displayResults.map((product, index) => {
              const isUnavailable = product.price_val >= 999999999;
              const isBestDeal   = !isUnavailable && product.price_val === bestDealPrice;
              const siteColor    = SITE_COLORS[product.site] || '#38bdf8';

              return (
                <a
                  key={index}
                  href={product.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`product-card ${isBestDeal ? 'best-deal' : ''} ${isUnavailable ? 'unavailable' : ''}`}
                  style={{ '--site-color': siteColor }}
                >
                  {/* Product Image */}
                  {product.image ? (
                    <img
                      src={product.image}
                      alt={product.name}
                      className="product-image"
                      onError={(e) => { e.target.style.display='none'; e.target.nextSibling.style.display='flex'; }}
                    />
                  ) : null}
                  <div
                    className="product-image-placeholder"
                    style={{ display: product.image ? 'none' : 'flex' }}
                  >
                    <ImageIcon size={32} />
                  </div>

                  {/* Info */}
                  <div className="product-info">
                    <h3 className="product-title">{product.name}</h3>
                    <span
                      className="product-site"
                      style={{ background: `${siteColor}22`, color: siteColor, borderColor: `${siteColor}44` }}
                    >
                      {product.site}
                    </span>
                    {isBestDeal && (
                      <span className="best-deal-badge">
                        <TrendingDown size={14} /> Best Deal
                      </span>
                    )}
                  </div>

                  {/* Price */}
                  <div className={`product-price ${isUnavailable ? 'unavailable-price' : ''}`}>
                    {isUnavailable ? '—' : product.price_str}
                  </div>

                  {/* CTA */}
                  <div className={`product-action ${isBestDeal ? 'product-action-best' : ''} ${isUnavailable ? 'product-action-dim' : ''}`}>
                    {isUnavailable ? 'Check Site' : 'View Deal'} <ExternalLink size={14} style={{ display:'inline', marginLeft:'4px', verticalAlign:'text-bottom' }} />
                  </div>
                </a>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
