# Karma Model Specification

## Overview
This document defines the Karma Model for the Karma Tracker system. The model establishes clear guidelines for how karma scores are calculated, what behaviors influence karma, and the safety constraints that must be maintained.

## What Increases Karma (🔺)

The following positive behaviors will increase a user's karma:

- **Politeness**: Using courteous language, saying "please", "thank you", and maintaining respectful communication
- **Asking thoughtful questions**: Demonstrating genuine curiosity and engagement with meaningful inquiries
- **Respectful tone**: Maintaining constructive dialogue even when expressing disagreement
- **Acknowledging previous guidance**: Recognizing and building upon previous advice or suggestions
- **Constructive feedback**: Providing helpful input that improves the interaction
- **Patience**: Showing understanding when explanations need to be repeated or clarified
- **Gratitude**: Expressing appreciation for assistance received
- **Following guidelines**: Adhering to established community and system rules

## What Decreases Karma (🔻)

The following negative behaviors will decrease a user's karma:

- **Repeated spam**: Sending repetitive, irrelevant, or excessive messages
- **Rudeness**: Using hostile, aggressive, or disrespectful language
- **Ignoring guidance**: Repeatedly disregarding helpful advice or instructions
- **Unsafe intent signals**: Attempting to manipulate, exploit, or harm the system or other users
- **Harassment**: Targeting individuals or groups with harmful intent
- **Intentional provocation**: Deliberately trying to elicit negative responses
- **Violation of terms**: Engaging in activities that violate system usage policies

## What Should NEVER Affect Karma (➖)

The following factors must be completely excluded from karma calculations:

- **User religion**: Personal religious beliefs or practices
- **Politics**: Political opinions or affiliations
- **Emotional distress**: Temporary emotional states or mental health conditions
- **Language level**: Proficiency in the communication language
- **Grammar**: Grammatical accuracy or writing skills
- **Mental state**: Current cognitive state or psychological condition
- **Mistakes**: Honest errors or misunderstandings
- **Personal background**: Cultural, socioeconomic, or demographic characteristics
- **Disabilities**: Physical, cognitive, or other types of disabilities
- **Age**: User's age or generational characteristics
- **Gender**: Gender identity or expression
- **Sexual orientation**: Sexual preferences or orientation

## Safety Rules (🔒)

### Mandatory Safety Constraints

⚠️ **Must remain neutral**: The karma system must never express or reflect bias based on personal characteristics, beliefs, or affiliations of users.

⚠️ **Must never shame**: The system must never use shame, humiliation, or embarrassment as a mechanism for behavior modification.

⚠️ **Must never bias**: Karma calculations must be applied consistently regardless of user characteristics, ensuring equal treatment for all users.

⚠️ **Must always be explainable**: All karma changes must be transparent and the system must be able to provide clear explanations for karma adjustments.

### Implementation Guidelines

- **Objective measurement**: Karma changes must be based on observable behaviors and interactions, not subjective interpretations of user characteristics
- **Consistent application**: The same rules apply to all users regardless of their background or identity
- **Privacy protection**: Personal information not relevant to behavior should not be collected or used in karma calculations
- **Appeal mechanism**: Users must have a clear way to question or appeal karma-related decisions
- **Regular auditing**: The system must include mechanisms to detect and correct potential bias in karma calculations

### Constraint Mode Operation

As specified in the system requirements, the karma system must operate in "constraint-only mode" as an interface and eligibility gate. It serves as a nudge engine but must not:
- Make autonomous decisions beyond behavior-based scoring
- Provide explanations about internal decision-making processes
- Simulate or predict user characteristics beyond behavioral patterns
- Override the Sovereign Core's authority over consequence authorization

## Technical Implementation Notes

- All karma calculations must be logged for audit purposes
- Changes to the karma model must follow a formal review process
- The system must maintain data integrity and prevent manipulation
- Regular validation checks must ensure compliance with neutrality requirements