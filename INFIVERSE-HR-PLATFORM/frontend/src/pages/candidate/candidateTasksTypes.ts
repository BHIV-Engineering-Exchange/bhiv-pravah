/** UI types for candidate tasks; map from API responses after integration. */

export type WorkflowTaskStatus = 'Pending' | 'In Progress' | 'Completed'

export type TaskPriority = 'High' | 'Medium' | 'Low'

export type SubmissionReviewStatus = 'Pending Review' | 'Approved' | 'Rejected'

export interface CandidateTaskSubmission {
  id: string
  status?: SubmissionReviewStatus
  githubLink?: string
  documentLink?: string
  feedback?: string
}

export interface CandidateWorkflowTask {
  id: string
  title: string
  description: string
  workflowStatus: WorkflowTaskStatus
  priority: TaskPriority
  progress: number
  dueDate: string
  department?: string
  jobTitle?: string
  submission?: CandidateTaskSubmission | null
}

export type TaskFilterTab = 'all' | 'pending' | 'inprogress' | 'submitted' | 'completed'
