const axios = require('axios');
const cheerio = require('cheerio');

class PolicyRetrieverTool {
    constructor() {
        this.cache = new Map();
    }

    /**
     * Retrieve and extract relevant passages from a pricing page
     * @param {string} url - URL of the pricing page
     * @param {string} query - Search query to find relevant content
     * @param {number} k - Number of passages to return (default: 5)
     * @returns {Object} Result with success, data, error, source, ts
     */
    async retrieve(url, query, k = 5) {
        try {
            const cacheKey = `${url}_${query}`;
            if (this.cache.has(cacheKey)) {
                const cached = this.cache.get(cacheKey);
                return {
                    success: true,
                    data: cached,
                    source: url,
                    ts: new Date().toISOString()
                };
            }

            const response = await axios.get(url, {
                timeout: 10000,
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            });

            const $ = cheerio.load(response.data);
            
            const textContent = this.extractTextContent($);
            
            const passages = this.findRelevantPassages(textContent, query, k);
            
            const result = {
                passages: passages
            };

            this.cache.set(cacheKey, result);

            return {
                success: true,
                data: result,
                source: url,
                ts: new Date().toISOString()
            };

        } catch (error) {
            return {
                success: false,
                error: `Failed to retrieve policy: ${error.message}`,
                source: url,
                ts: new Date().toISOString()
            };
        }
    }

    /**
     * Extract text content from HTML, focusing on pricing-related sections
     * @param {Object} $ - Cheerio object
     * @returns {Array} Array of text sections
     */
    extractTextContent($) {
        const sections = [];
        
        const pricingSelectors = [
            'h1, h2, h3, h4, h5, h6',
            '.pricing, .price, .cost, .membership, .plan',
            '.subscription, .pass, .membership',
            'p, div, span, li',
            'table, .table'
        ];

        pricingSelectors.forEach(selector => {
            $(selector).each((i, element) => {
                const text = $(element).text().trim();
                if (text.length > 10 && text.length < 500) {
                    sections.push({
                        text: text,
                        tag: element.tagName,
                        className: $(element).attr('class') || '',
                        id: $(element).attr('id') || ''
                    });
                }
            });
        });

        return sections;
    }

    /**
     * Find passages relevant to the query
     * @param {Array} textContent - Array of text sections
     * @param {string} query - Search query
     * @param {number} k - Number of passages to return
     * @returns {Array} Array of relevant passages with scores
     */
    findRelevantPassages(textContent, query, k) {
        const queryTerms = query.toLowerCase().split(/\s+/);
        
        const scoredPassages = textContent.map(section => {
            const text = section.text.toLowerCase();
            let score = 0;
            
            queryTerms.forEach(term => {
                if (text.includes(term)) {
                    score += 1;
                }
            });

            const pricingKeywords = [
                'price', 'cost', 'fee', 'charge', 'membership', 'subscription',
                'monthly', 'annual', 'per ride', 'per minute', 'unlock',
                'ebike', 'electric', 'classic', 'dollar', '$', 'minute',
                'hour', 'day', 'week', 'overage', 'surcharge'
            ];

            pricingKeywords.forEach(keyword => {
                if (text.includes(keyword)) {
                    score += 0.5;
                }
            });

            if (['h1', 'h2', 'h3'].includes(section.tag)) {
                score += 2;
            }
            if (['h4', 'h5', 'h6'].includes(section.tag)) {
                score += 1;
            }

            return {
                text: section.text,
                source: `${section.tag}${section.className ? '.' + section.className : ''}${section.id ? '#' + section.id : ''}`,
                score: score
            };
        });

        return scoredPassages
            .filter(p => p.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, k);
    }
    clearCache() {
        this.cache.clear();
    }
}

module.exports = PolicyRetrieverTool;
