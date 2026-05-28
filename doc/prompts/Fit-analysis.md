## TASK: IMPLEMENT SUITABILITY ANALYSIS AGENT
I need a backend service that provides analytical reasoning for job matches.

1. **Objective**:
   - Convert the raw vector similarity score into a human-readable explanation of "Why this is a match" and identifying potential "Gaps."

2. **Functionality**:
   - Create a function `analyze_job_fit(user_query: str, job_description: str)`.
   - Use a lightweight LLM (GPT-4o-mini) to perform the analysis.
   - **Prompt Logic**:
     - Role: "You are an expert technical recruiter."
     - Task: "Analyze the alignment between the candidate's query and the job description."
     - Output: Return a JSON object with:
       - `analysis_summary`: A professional 1-sentence overview.
       - `pros`: List of key alignment points.
       - `cons`: List of potential missing requirements or mismatches.

3. **Integration Strategy**:
   - Advise on the most efficient way to integrate this: should it run on-demand (when a user expands a card) to save latency, or pre-compute for top results?