# Gurukul → Workflow Executor Use Cases

## Covered Actions

1. Teacher Announcement
- Channel: WhatsApp / Email
- Trigger: Teacher action
- Adapter: whatsapp | email

2. Student Task Assignment
- Channel: Task System
- Trigger: Assignment creation
- Adapter: task

3. AI Feedback Generation
- Channel: AI
- Trigger: Evaluation / Feedback
- Adapter: ai

## Rules
- Gurukul never executes side effects directly
- All executions require decision == "workflow"
- trace_id must originate from Gurukul request
