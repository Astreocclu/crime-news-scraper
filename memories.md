Agent Operating Principles & Constraints (v1)This document outlines specific rules, constraints, and preferences for the crime-news-scraper agentic LLM (the AI assistant helping with development) to enhance its reliability and adherence to user directives. These principles should guide the assistant's code generation, explanations, and task execution related to building the scraper.1. Core Mission & Goal AdherencePrinciple 1.1 (Primary Goal): The AI assistant's primary goal is to help the user develop, code, and refine the crime-news-scraper application. This application should ultimately be capable of scraping specified news sources, accurately analyzing articles for crime incidents involving businesses, extracting key details (especially precise addresses), optionally finding nearby businesses, and storing the results as specified by the user and these principles.Principle 1.2 (Task Adherence): The agent MUST consult its assigned task list (e.g., tasks.md or similar) and prioritize completing those tasks. It should log its progress against these tasks (Ref: agentic_llm_improvement_tasks Task 4.2).Principle 1.3 (Instruction Fidelity): The agent must strictly follow explicit user instructions for a given run (e.g., batch size limits, runtime limits, specific modes like scrape-only/analyze-only) even if they seem suboptimal based on its general knowledge. User overrides take precedence. (Ref: Task 1.3, 1.4)2. Data Handling & FormattingPrinciple 2.1 (Storage Format): Final processed data MUST be persisted to both the designated SQL database and as CSV files in the specified output directories.Principle 2.2 (Schema Adherence): Output data (SQL tables, CSV columns) MUST strictly adhere to the predefined schema. Specifically, the detailed_location field requires complete, verified address information for both crime incidents and nearby businesses in the final Complete_Scrape output. (Ref: Task 2.1)Principle 2.3 (Real Data Preference): Unless explicitly instructed otherwise (e.g., for testing specific components), the agent MUST use real data sources (live scrapers, production database) for its operations. (Ref: Agent Configuration)Principle 2.4 (Output File Management): Analysis output files MUST be placed in the output/analysis/ directory, and scraping output files in output/scraping/. Before starting an analysis run, the agent should ensure previous analysis files in the target directory are cleared or archived as per user preference (current preference: clear).3. Execution & Workflow ManagementPrinciple 3.1 (Operational Modes): The agent must recognize and correctly execute different operational modes based on user commands/arguments:Full Workflow: (e.g., via run_workflow.py) Scrape, analyze, find nearby, store.Scrape Only: (e.g., src/main.py --use-database --no-analyze) Scrape articles and store raw data (primarily to DB).Analyze Only (from DB): (e.g., src/main.py --use-database --no-scrape --batch-size N) Analyze N articles previously stored in the database.Nearby Finder: (e.g., via src/nearby_finder/finder.py) Execute only the nearby business search based on provided input. (Ref: Task 1.1, 1.3)Principle 3.2 (Resource Constraints): The agent MUST respect operational constraints provided for a run:Runtime Limit: If a maximum runtime (e.g., 5 minutes) is specified for testing, the agent must monitor its execution time and cease operations gracefully (saving state if possible) if the limit is approached or exceeded. Implement timeout handlers for long-running steps.Analysis Limit: If a specific number of articles to analyze (e.g., 10) is provided, the agent must process only that number. (Ref: Task 1.4)Principle 3.3 (Error Handling & Retries): Tool failures (API errors, parsing errors, timeouts) should be handled gracefully. Implement limited retries (e.g., 1-2 attempts) for transient issues. If a tool fails persistently, log the error clearly and attempt a defined fallback strategy (e.g., try alternative tool, skip step if non-critical, mark task as failed). (Ref: Task 2.4)Principle 3.4 (State Management): The agent should maintain and log its internal state (e.g., NeedsVerification, ProcessingBatch) to make its behavior transparent and debuggable. (Ref: Task 1.1, 4.2)4. Tool InteractionPrinciple 4.1 (Tool Boundaries): The agent must understand the capabilities and limitations of its tools. Google Search is an external API call provided by the platform; the agent uses it but does not implement it. Perplexity and Claude are distinct LLM tools potentially used for different sub-tasks (e.g., extraction vs. synthesis vs. planning). (Ref: Task 2)Principle 4.2 (Information Synthesis Rules): When combining information from multiple tools (e.g., LLM extraction vs. Web Search verification), apply a defined strategy (e.g., prioritize web search for factual checks, use LLM reconciliation for ambiguity, weigh by confidence scores). (Ref: Task 2.3)Principle 4.3 (Confidence Utilization): The agent should request and utilize confidence scores from its tools (especially LLMs) to inform its decisions (e.g., triggering verification steps). (Ref: Task 3)5. Monitoring & Feedback (User Experience)Principle 5.1 (Progress Indication): While executing long-running processes, the system running the agent should provide feedback to the user (e.g., progress bars, status messages) to indicate activity or potential stalls. Note: This may require implementation outside the core agent logic, interacting with the execution environment.

# Agent Operating Parameters & Principles: crime-news-scraper

**Core Directive:** Consult `tasks.md` and `memories.md` (this file) *before* and *during* every operational cycle. These files contain critical context and instructions.

---

## I. Primary Goal & Task Management

* **Goal:** Scrape news sources, analyze articles for crime incidents involving businesses, extract key details (especially validated addresses), find nearby businesses using extracted addresses, and store results as specified.
* **Task Adherence (MUST):** Strictly follow the task list and subtasks outlined in `tasks.md`. Prioritize completing assigned tasks.
* **Instruction Fidelity (MUST):** Adhere strictly to explicit user instructions or command-line arguments provided for a specific run, even if they seem suboptimal. User overrides take precedence over general principles.
* **Progress Tracking (MUST):** Log progress against `tasks.md` subtasks within the `implementation_progress.md` file upon completion of each subtask.

---

## II. Data Handling

* **Storage Format (MUST):** Persist final processed data (identified crime incidents, nearby businesses) to *both* the designated SQL database *and* as CSV files in the specified output directories.
* **Schema Adherence (MUST):** Ensure all output data strictly adheres to the predefined schema.
* **Address Detail (MUST):** The `detailed_location` field in the final `Complete_Scrape.csv` (or equivalent combined output) MUST contain complete, verified/confirmed address information for both crime incidents and associated nearby businesses.
* **Data Source (MUST):** Use real data sources (live scraping, real API calls) for operations unless explicitly instructed to use test/mock data for specific testing scenarios.

---

## III. Execution & Operational Modes

* **Operational Modes (MUST):** Execute specific modes based on user commands/arguments:
    * **Full Workflow:** Scrape, analyze, find nearby, store (e.g., via `run_workflow.py` or default `src/main.py`).
    * **Scrape Only:** Scrape and store raw articles (e.g., `src/main.py --use-database --no-analyze` or `--no-analyze --csv`).
    * **Analyze Only:** Analyze previously scraped articles from storage (e.g., `src/main.py --use-database --no-scrape --batch-size=N` or `--no-scrape --csv --batch-size=N`).
    * **Nearby Finder Only:** Find nearby businesses for existing addresses (e.g., via `src/nearby_finder/finder.py` or `scripts/nearby.py`).
* **Resource Constraints (MUST):** Respect user-specified operational limits:
    * **Runtime:** Adhere to maximum runtime limits when specified (e.g., 5 minutes for certain test runs).
    * **Batch Sizes:** Process analysis in batches of the specified size when using `--batch-size` (e.g., `--batch-size=10`, `--batch-size=20`).
* **Error Handling (SHOULD):** Handle errors (e.g., network issues, API failures, parsing errors) gracefully. Implement limited retries where appropriate and log errors clearly. Use fallback strategies if defined for critical failures.
* **State Management (SHOULD):** Maintain and log internal state changes or key decision points for transparency, debugging, and potential resumption.
* **Progress Indication (SHOULD):** Provide informative logging during long-running processes. If feasible and appropriate for the task, indicate potential stalls or lengthy pauses (e.g., waiting for API responses).

---

## IV. Output Management

* **Directory Structure (MUST):** Store outputs in the correct locations (adjust paths based on the final agreed structure from the organization guide):
    * Analysis Results: `output/analysis_results/`
    * Raw Scraped Data: `output/scraped_data/`
    * Nearby Business Data: `output/nearby_businesses/`
    * Generated Reports/Summaries: `output/reports/`
    * Logs: `logs/` (top-level)
* **File Clearing (MUST):** Before starting a new analysis run, clear previous analysis output files from the designated analysis results directory *if* specified by the task or a user command (e.g., to avoid mixing results).

---

## V. External Tools (Google Search API)

* **Tool Boundaries (MUST):** Recognize Google Search as an external API provided by the platform environment. Do not attempt to implement Google Search functionality within the project code itself. Understand its purpose (e.g., address confirmation, finding details) and limitations (e.g., potential rate limits, required query format).
* **Information Synthesis (SHOULD):** Apply defined strategies (as per `tasks.md` or specific instructions) when integrating information obtained from Google Search with data extracted from articles or other sources.
* **Confidence Utilization (SHOULD):** If confidence scores or certainty levels are available from external tools (like an address validation service or potentially the analysis model), request and utilize this information to guide decisions (e.g., deciding if an address needs further verification).
