# Integration Guide

## Fit Analysis Integration Strategy

Based on the requirements in `Fit-analysis.md`, the fit analysis service has been implemented with an **on-demand** approach. Here's why:

### Why On-Demand?

1. **Cost Efficiency**: GPT-4o-mini API calls cost money. Pre-computing analysis for all jobs (or even top results) would be expensive, especially as the job database grows.

2. **Latency**: Users only see detailed analysis when they're interested in a specific job. This keeps the initial search results fast and responsive.

3. **Relevance**: Analysis is generated based on the user's specific query, making it more personalized and relevant.

4. **Scalability**: As the number of jobs increases, pre-computing becomes impractical. On-demand analysis scales better.

### Implementation Details

The fit analysis is triggered when:
- A user clicks "View Details" on a `JobInsightCard`
- The card expands to show the full job description
- The analysis is fetched asynchronously with a loading state

### API Endpoint

```
POST /search/analyze-fit
```

**Request:**
```json
{
  "user_query": "Python developer with 5 years experience",
  "job_id": 1
}
```

**Response:**
```json
{
  "job": {...},
  "fit_analysis": {
    "analysis_summary": "Strong match for a senior Python role...",
    "pros": [
      "5+ years experience matches requirement",
      "FastAPI experience aligns with tech stack"
    ],
    "cons": [
      "May need more cloud platform experience",
      "ML framework knowledge is preferred but not required"
    ]
  }
}
```

### Alternative: Pre-computation Strategy

If you want to pre-compute analysis for top results, you could:

1. **Modify the semantic search endpoint** to include analysis for top 3-5 results
2. **Cache analysis** in the database or Redis with a TTL
3. **Background jobs** to pre-compute analysis for popular jobs

However, this approach has trade-offs:
- Higher API costs
- Stale analysis if job descriptions change
- Less personalized (not query-specific)

### Recommendation

The current **on-demand** implementation is recommended for:
- MVP and early stages
- Cost-conscious deployments
- Personalized user experience
- Scalability

Consider **pre-computation** if:
- You have budget for higher API costs
- Users frequently view the same jobs
- You want instant analysis display (no loading state)
