# Invesco Insights Clustering Analysis

## Business Case

Editorial content on our website is tagged poorly on the backend. This hampers analysis and subsequent decision-making. We need to accomplish two things:

1. Understand the underlying themes within our content
2. Turn those themes into tags that can be properly applied to content either manually or programmatically (the latter to optimize tag enforcement)

## Proposed Solution

Utilize data science, and more specifically, machine learning to algorithmically cluster this content as an exploratory analysis to uncover potiential theme candidates.


## Project Status

A code base refactor is currently ongoing that includes the following action items:

1. Adding doc strings to all functions, methods, and classes for legibility
2. Building out markdown within the second version of the notebook to better tell the story of this analysis
3. Optimization of model with feature engineering, data enrichment, and/or regularization
4. Explaining the mathematical foundation for decision-making
5. Implementation of K-Means Error to select optimal model run by analyzing total intra cluster variance
6. Implementing testing via doctests or unit testing is on the wishlist but is not mission critical given the business case (nice to have, not a must have)

There are others that will be added to this list as the project progresses.
