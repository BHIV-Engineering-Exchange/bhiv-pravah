This document defines how Prompt Runner classifies user prompts into modules and intents.

Prompt Runner converts user prompts into structured JSON instructions containing:

module

intent

topic

tasks

output_format

These rules ensure deterministic routing of prompts across different domains so the Core Integrator can execute the correct system module.

Domain → Module Mapping

education → explain / learning
finance → financial analysis
creator → content generation
workflow → system design
development → software tasks
healthcare → diagnosis / treatment guidance
legal → legal analysis / compliance guidance
architecture → building design / site planning
data → data analysis / insights generation
business → strategy / market analysis
marketing → campaign planning / promotion strategy

Domain Details
Education

Example Prompts

Explain Newton’s laws of motion
Teach the basics of machine learning
Create a study plan for learning Python

Keywords

explain
teach
learn
study
concept
tutorial

Module

education

Intent

generate_explanation

Finance

Example Prompts

Calculate income tax for a salary of 18 lakh
Analyze investment risk for a portfolio
Explain stock market basics

Keywords

tax
investment
finance
profit
income
financial

Module

finance

Intent

financial_analysis

Software Development

Example Prompts

Build a stock prediction application
Design a mobile app architecture
Create a REST API backend

Keywords

build
software
app
coding
architecture
backend
development

Module

development

Intent

system_design

Workflow / System Design

Example Prompts

Design a customer support workflow
Create an inventory management process
Develop an automation pipeline

Keywords

workflow
process
pipeline
automation
system

Module

workflow

Intent

process_design

Content Creation

Example Prompts

Write a blog about AI in healthcare
Create a YouTube video script
Generate a marketing article

Keywords

write
blog
content
article
script
outline

Module

creator

Intent

content_generation

Architecture

Example Prompts

Design a residential tower in Mumbai
Create a layout for a commercial office building

Keywords

design
building
architecture
structure
construction

Module

architecture

Intent

design_planning

Healthcare

Example Prompts

Explain early symptoms of diabetes
Create a workflow for diagnosing hypertension

Keywords

diagnosis
treatment
medical
symptoms
health

Module

healthcare

Intent

diagnosis_guidance

Legal

Example Prompts

Explain the legal process for filing a consumer complaint
Analyze compliance requirements for a business

Keywords

law
legal
compliance
court
regulation

Module

legal

Intent

legal_analysis

Data Analysis

Example Prompts

Analyze sales data for the last quarter
Identify trends in website traffic data

Keywords

data
analysis
dataset
metrics
statistics

Module

data

Intent

data_analysis

Business Strategy

Example Prompts

Create a market entry strategy for a new product
Analyze the competitive landscape for a startup

Keywords

business
strategy
market
planning
competition

Module

business

Intent

strategy_analysis

Marketing

Example Prompts

Create a digital marketing campaign for a mobile app
Develop a social media promotion strategy

Keywords

marketing
campaign
promotion
advertising
brand

Module

marketing

Intent

campaign_planning

Deterministic Classification Rule

Prompt Runner determines prompt classification using:

keyword detection

prompt context

task objective

Identical prompts must always produce the same module and intent mapping to ensure consistent routing across platform systems.