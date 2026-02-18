# Specification: Usage Statistics Tracking & Reporting

## Overview
Implement a persistent system to track, aggregate, and display user transcription statistics. This feature provides insights into how the app is used over time, categorized by daily, monthly, and lifetime metrics.

## Functional Requirements
- **Data Persistence**: Store statistics in a persistent JSON file within the user's local AppData directory (`%AppData%/ParrotInk/stats.json`).
- **Metric Collection**:
    - **Total Transcriptions**: Incremented every time a session completes successfully.
    - **Total Duration**: Cumulative time spent in the `LISTENING` state.
    - **Provider Usage**: Track the number of successful transcriptions per provider (OpenAI, AssemblyAI, etc.).
    - **Error Count**: Track failed transcription attempts (network errors, API failures).
    - **Word Count**: Total count of words generated across all transcriptions.
- **Reporting Tiers**:
    - Data must be aggregated and displayable for **Today**, **This Month**, and **Lifetime**.
- **User Interface**:
    - Add a "Statistics" item to the System Tray menu.
    - Selecting "Statistics" opens a modern dialog box (using `tkinter` or similar) displaying the aggregated metrics in a clear, readable format.

## Non-Functional Requirements
- **Low Overhead**: Statistics updates should happen asynchronously or at the end of a session to avoid adding latency to the transcription pipeline.
- **Resilience**: The app should handle missing or corrupted `stats.json` files gracefully by re-initializing them.

## Acceptance Criteria
- [ ] A `stats.json` file is created and updated correctly after each session.
- [ ] The Tray Menu contains a working "Statistics" entry.
- [ ] The Statistics dialog correctly displays separate values for Daily, Monthly, and Lifetime metrics.
- [ ] Statistics accurately reflect provider usage and word counts.

## Out of Scope
- Detailed graph/chart visualizations (text-based report only for now).
- Cloud syncing of statistics across devices.
