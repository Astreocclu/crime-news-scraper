# Perplexity API Address Validation Evaluation

This directory contains scripts and data for evaluating the Perplexity API address validation functionality in the crime news scraper application.

## Overview

The Perplexity API address validation functionality is designed to enhance address information for crime incidents at jewelry stores by querying the Perplexity API with business names and locations to obtain accurate address information. This evaluation assesses the effectiveness of this functionality and identifies areas for improvement.

## Directory Structure

- `create_sample.py`: Script to create a sample of articles for evaluation
- `run_evaluation.py`: Script to run the evaluation
- `ground_truth.json`: Manually verified addresses for a subset of articles
- `sample_articles.csv`: Sample of articles for evaluation
- `results/`: Directory containing evaluation results
  - `evaluation_results_*.csv`: Detailed results for each article
  - `evaluation_metrics_*.json`: Summary metrics for the evaluation
  - `comparison_table.md`: Comparison of results vs. ground truth
  - `final_comparison_table.md`: Final comparison after refinements
- `summary_of_findings.md`: Summary of evaluation findings

## Evaluation Process

1. **Sample Creation**: A sample of 20 articles is created from the scraped data, including articles from JSA and Review Journal sources.

2. **Ground Truth**: Addresses for a subset of articles are manually verified to create a ground truth dataset.

3. **Evaluation Script**: The evaluation script processes each article, queries the Perplexity API if needed, and compares the results with the ground truth.

4. **Metrics**: The evaluation measures the success rate, API query triggering rate, and address improvement rate.

5. **Refinement**: Based on the evaluation results, refinements are implemented to improve the functionality.

## Implementation Details

### Perplexity API Integration

The Perplexity API integration is implemented in `src/perplexity_client.py` and consists of:

1. **PerplexityClient Class**: A client for the Perplexity API that handles authentication and API calls.

2. **get_address Method**: Sends a structured prompt to the Perplexity API and extracts the address from the response.

3. **Error Handling**: Robust error handling for API failures, rate limiting, and invalid responses.

### Address Enhancement Process

The address enhancement process in `src/analyzer/analyzer_manual_test.py` follows these steps:

1. **Trigger Determination**: Determines if address enhancement is needed based on missing or low-confidence addresses.

2. **Prompt Generation**: Creates a structured prompt with business name, location, and other relevant information.

3. **API Query**: Sends the prompt to the Perplexity API via the PerplexityClient.

4. **Response Processing**: Extracts and normalizes the address from the API response.

5. **Confidence Assessment**: Assigns a confidence score based on validation checks.

6. **Analysis Update**: Updates the analysis with the enhanced address information.

## Running the Evaluation

To run the evaluation:

```bash
python3 evaluation/run_evaluation.py
```

This will process the sample articles, query the Perplexity API as needed, and generate evaluation results in the `results/` directory.

## Results

The evaluation of the Perplexity API address validation functionality will measure:

1. **Accuracy**: How accurately the Perplexity API returns the correct address compared to ground truth.
2. **Completeness**: Whether the returned addresses include all necessary components (street, city, state, zip).
3. **Response Time**: How quickly the API responds to queries.
4. **Success Rate**: The percentage of queries that successfully return usable addresses.

## Recommendations

Based on initial implementation, the following recommendations are made for optimizing the functionality:

1. **Prompt Engineering**: Refine the prompts sent to Perplexity API to improve address accuracy.
2. **Error Handling**: Implement robust error handling for API failures or rate limiting.
3. **Response Validation**: Add validation checks to ensure returned addresses are properly formatted.
4. **Caching**: Consider implementing a caching mechanism to reduce API calls for repeated queries.
5. **Fallback Mechanism**: Implement a fallback to other address validation methods if Perplexity API fails.

## Conclusion

The Perplexity API address validation functionality provides a more reliable and accurate method for validating addresses compared to the previous web search approach. By implementing the recommendations above, the functionality can be further optimized for production use.
