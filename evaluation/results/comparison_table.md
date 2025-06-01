# Web Search Address Validation Comparison Table

## Summary
- **Total Articles Evaluated**: 20
- **Web Search Triggered**: 20 (100.0%)
- **Correct Addresses**: 0 (0.0%)
- **Addresses Improved by Web Search**: 0 (0.0% of triggered searches)

## Detailed Comparison

| Article Title | Ground Truth Address | Initial Address | Web Search Triggered | Final Address | Correct? | Address Source |
|---------------|----------------------|-----------------|----------------------|---------------|----------|----------------|
| KENSINGTON, MD- Police investigating burglary at Kensington jewelry store. | Raffie Jewelers<br>3774 Howard Ave, Kensington, MD 20895 | unknown | Yes | unknown | No | - |
| Jeweler Shot and Killed in Sacramento, CA | Kim Tin Jewelry<br>6830 Stockton Blvd, Suite 190, Sacramento, CA 95823 | unknown | Yes | unknown | No | - |
| GASTONIA, NC – ATT. BURGLARY OF JEWELRY KIOSK. | Jewelry Kiosk at Eastridge Mall<br>246 N New Hope Rd, Gastonia, NC 28054 | unknown | Yes | unknown | No | - |
| San Carlos, CA- : 18-year-old arrested in $56,000 jewelry store robbery. | Home Consignment Center<br>1123 Industrial Road, San Carlos, CA 94070 | unknown | Yes | unknown | No | - |
| PULALLUP, WA- BURGLARY AT THE SOUTH HILL MALL. | South Hill Mall<br>3500 S Meridian, Puyallup, WA 98373 | unknown | Yes | unknown | No | - |
| $80K Worth Of Jewelry Stolen From Langley Park Shop, Suspect Sought: PGPD | Langley Park Jewelry Store<br>1400 University Blvd E, Langley Park, MD 20783 | unknown | Yes | unknown | No | - |

## Analysis of Results

The evaluation shows that the web search address validation functionality is not working effectively:

1. **Web Search Triggering**: The web search was triggered for all articles (100%), which is expected since all initial addresses were set to "unknown" with "low" confidence.

2. **Address Extraction**: Despite the web search being triggered, no addresses were successfully extracted from the search results. This indicates a problem with the address extraction logic or the search results themselves.

3. **Success Rate**: The success rate is 0%, meaning none of the addresses were correctly identified through web search.

## Potential Issues

Based on the evaluation results, the following issues may be affecting the web search address validation:

1. **Mock Web Search Results**: The mock web search function in test_web_search.py always returns the same results about a Palm Desert jewelry store robbery, regardless of the query. This doesn't provide relevant results for the specific articles being analyzed.

2. **Address Extraction Patterns**: The regular expression patterns used for address extraction may not be matching the formats in the search results.

3. **Location Context**: The location information from the articles is not being properly incorporated into the search queries or address validation.

4. **Business Name Recognition**: The business names are not being effectively extracted or used in the search process.

These issues will be addressed in the refinement phase to improve the web search address validation functionality.
