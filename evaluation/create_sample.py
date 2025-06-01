#!/usr/bin/env python3
"""
Create a sample dataset for evaluating the web search address validation.
"""

import pandas as pd
import random
import os
import json

# Set random seed for reproducibility
random.seed(42)

# Input file paths
jsa_articles_path = "output/jsa_articles_20250411_183644.csv"
reviewjournal_articles_path = "output/reviewjournal_articles_20250411_183644.csv"

# Output file paths
sample_articles_path = "evaluation/sample_articles.csv"
ground_truth_path = "evaluation/ground_truth.json"

def create_sample():
    """Create a sample of articles for evaluation."""
    # Load the articles
    jsa_df = pd.read_csv(jsa_articles_path)
    reviewjournal_df = pd.read_csv(reviewjournal_articles_path)
    
    # Filter for articles that are theft-related and business-related
    jsa_filtered = jsa_df[jsa_df['is_theft_related'] == True]
    jsa_filtered = jsa_filtered[jsa_filtered['is_business_related'] == True]
    
    # Select a random sample of 15 articles from JSA
    jsa_sample = jsa_filtered.sample(n=min(15, len(jsa_filtered)))
    
    # Select a random sample of 5 articles from Review Journal
    reviewjournal_sample = reviewjournal_df.sample(n=min(5, len(reviewjournal_df)))
    
    # Combine the samples
    combined_sample = pd.concat([jsa_sample, reviewjournal_sample], ignore_index=True)
    
    # Save the sample to CSV
    combined_sample.to_csv(sample_articles_path, index=False)
    
    print(f"Created sample of {len(combined_sample)} articles in {sample_articles_path}")
    
    # Create an empty ground truth file
    ground_truth = {}
    for _, article in combined_sample.iterrows():
        article_id = article.get('url', '')
        if not article_id:
            continue
            
        ground_truth[article_id] = {
            "business_name": "",
            "full_address": "",
            "notes": "Please manually verify and fill in this information"
        }
    
    # Save the ground truth template
    with open(ground_truth_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"Created ground truth template in {ground_truth_path}")
    print("Please manually fill in the business names and addresses in the ground truth file.")

if __name__ == "__main__":
    create_sample()
