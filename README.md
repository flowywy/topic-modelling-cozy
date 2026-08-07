# Cozy Game Review Analysis using BERTopic
An NLP-based project for discovering player opinions and discussion topics from mobile cozy game reviews on Google Play Store using BERTopic.

## Overview
This project applies BERTopic to identify dominant topics, analyze sentiment distribution, and explore temporal trends in player reviews of cozy games.

The dataset consists of English-language reviews collected from Google Play Store. The analysis focuses on eight mobile cozy games representing four game segments.

## Methodology
The project follows the CRISP-DM framework:

- Data collection from Google Play Store
- Text preprocessing
- Topic modeling using BERTopic
- Topic evaluation using:
  - C_V coherence score
  - Topic diversity
  - Topic similarity analysis
  - Inference evaluation
- Interactive deployment using Streamlit

## Model Configuration
- Embedding model: `all-mpnet-base-v2`
- Topic modeling framework: BERTopic
- Representation model: KeyBERTInspired
- Dimensionality reduction: UMAP
- Clustering: HDBSCAN
- Topic representation: c-TF-IDF

## Results
The model generated 9 interpretable topics with:

- C_V coherence score: **0.5963**
- Topic diversity: **0.9111**
- Reduced outlier ratio: **38% → 25%**

The dominant topics include:
- General Experience and Game Content
- Technical Performance
- Relaxing and Stress-Relief Experience
- Ads and Monetization

## Demo Application
The trained model is deployed through a Streamlit application for interactive exploration of topic modeling results.

Demo: https://cozy-game-topics.streamlit.app/

## Technologies
- Python
- BERTopic
- Sentence Transformers
- UMAP
- HDBSCAN
- Streamlit
- Pandas
- Scikit-learn
