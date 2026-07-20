# AI Scoring Logic

## 1. Overview

The AI-driven scoring system in Infiverse is designed to provide an objective measure of employee productivity and focus during work hours. The system analyzes various data points collected through the monitoring service and assigns a score based on predefined rules and patterns. This document outlines the logic behind the scoring.

## 2. Data Points Analyzed

The AI model considers the following data points for its analysis:

- **Application Usage**: The name of the active application on the user's screen (e.g., `Visual Studio Code`, `Google Chrome`, `Slack`).
- **Website Visits**: The title and URL of the active browser tab.
- **Keystroke Frequency**: The rate of typing (keystrokes per minute).
- **Idle Time**: Periods with no keyboard or mouse activity.
- **Task Relevance**: The AI's assessment of whether the current activity is relevant to the user's assigned tasks for the day.

## 3. Scoring Categories

Websites and applications are categorized to determine their impact on the productivity score:

- **Productive**: Directly related to work (e.g., IDEs, design software, official communication channels, work-related websites).
- **Neutral**: General-purpose tools that can be used for both work and personal tasks (e.g., search engines, generic news sites).
- **Non-Productive**: Clearly unrelated to work (e.g., social media, video streaming sites, gaming sites).

These categories are maintained in the `WebsiteWhitelist` collection in the database and can be customized by administrators.

## 4. Scoring Calculation

The productivity score is calculated based on a weighted average of the time spent in each category:

- **Productive Time**: Time spent on productive applications and websites contributes positively to the score.
- **Idle Time**: Extended periods of inactivity negatively impact the score.
- **Non-Productive Time**: Time spent on non-productive sites significantly reduces the score.
- **Task Relevance**: The AI model uses the content of the screen (via OCR) and the application/website data to determine relevance to the user's assigned tasks. High relevance provides a bonus to the score, while low relevance may be flagged for review.

### Example:
An employee who spends most of their day in a code editor and on technical documentation sites, with minimal idle time, will have a high productivity score. Conversely, an employee who spends significant time on social media will have a low score.

## 5. Explainability

The system is designed to be transparent. When a low score is generated, the system provides an "explainability" report that breaks down the factors contributing to the score. This report includes:

- A chart showing the percentage of time spent in each productivity category.
- A list of the most frequently used non-productive applications or websites.
- Timestamps of significant idle periods.

This allows for fair and constructive conversations about performance and focus.
