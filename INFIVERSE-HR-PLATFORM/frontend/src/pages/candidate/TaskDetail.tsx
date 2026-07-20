import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useCandidateTasks } from '../../context/CandidateTasksContext'
import { fetchCandidateWorkflowTaskDetail, type WorkflowBridgeTask } from '../../services/api'
import type { CandidateTaskSubmission, CandidateWorkflowTask } from './candidateTasksTypes'

function toCandidateTask(row: WorkflowBridgeTask): CandidateWorkflowTask {
  const stOk = (s: string): s is CandidateWorkflowTask['workflowStatus'] =>
    s === 'Pending' || s === 'In Progress' || s === 'Completed'
  const prOk = (s: string): s is CandidateWorkflowTask['priority'] =>
    s === 'High' || s === 'Medium' || s === 'Low'
  const subSt = (s?: string): CandidateTaskSubmission['status'] | undefined => {
    if (s === 'Pending Review' || s === 'Approved' || s === 'Rejected') return s
    return undefined
  }
  return {
    id: row.id,
    title: row.title,
    description: row.description,
    workflowStatus: stOk(row.workflowStatus) ? row.workflowStatus : 'Pending',
    priority: prOk(row.priority) ? row.priority : 'Medium',
    progress: row.progress,
    dueDate: row.dueDate || new Date().toISOString(),
    department: row.department,
    jobTitle: row.jobTitle,
    submission: row.submission
      ? {
          id: row.submission.id,
          status: subSt(row.submission.status),
          githubLink: row.submission.githubLink,
          documentLink: row.submission.documentLink,
          feedback: row.submission.feedback,
        }
      : null,
  }
}

function IconArrowLeft({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
    </svg>
  )
}

function IconCalendar({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  )
}

function IconEye({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  )
}

function IconRefresh({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  )
}

function IconExternal({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
  )
}

function IconCheckSquare({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

export default function CandidateTaskDetail() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const { getTaskById, tasks } = useCandidateTasks()
  const [remoteTask, setRemoteTask] = useState<CandidateWorkflowTask | null>(null)
  const [loadingRemote, setLoadingRemote] = useState(false)

  const fromList = useMemo(
    () => (taskId ? getTaskById(taskId) : undefined),
    [taskId, getTaskById, tasks]
  )
  const task = fromList ?? remoteTask

  useEffect(() => {
    if (!taskId || fromList) {
      if (fromList) setRemoteTask(null)
      return
    }
    let cancelled = false
    setLoadingRemote(true)
    ;(async () => {
      try {
        const row = await fetchCandidateWorkflowTaskDetail(taskId)
        if (!cancelled) setRemoteTask(toCandidateTask(row))
      } catch {
        if (!cancelled) {
          setRemoteTask(null)
          toast.error('Could not load this task from the workflow API.', {
            id: 'candidate-workflow-task-detail',
            duration: 6000,
          })
        }
      } finally {
        if (!cancelled) setLoadingRemote(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [taskId, fromList])

  if (loadingRemote && !task) {
    return (
      <div className="space-y-4 p-4">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200 dark:bg-slate-700" />
        <div className="h-40 animate-pulse rounded-2xl bg-gray-100 dark:bg-slate-800" />
      </div>
    )
  }

  if (!task) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-gray-200 bg-white py-20 dark:border-slate-700 dark:bg-slate-800">
        <p className="text-lg font-medium text-gray-900 dark:text-white">Task not found</p>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">It may have been removed or the link is invalid.</p>
        <Link
          to="/candidate/tasks"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 px-5 py-2.5 text-sm font-medium text-white"
        >
          <IconArrowLeft className="h-4 w-4" />
          Back to My Tasks
        </Link>
      </div>
    )
  }

  const due = new Date(task.dueDate)
  const daysLeft = Math.ceil((due.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  const overdue = daysLeft < 0
  const submission = task.submission

  const statusClass =
    task.workflowStatus === 'Completed'
      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
      : task.workflowStatus === 'In Progress'
        ? 'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-300'
        : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'

  const priorityClass =
    task.priority === 'High'
      ? 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
      : task.priority === 'Medium'
        ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
        : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-cyan-400 dark:hover:text-cyan-300"
      >
        <IconArrowLeft className="h-4 w-4" />
        Back
      </button>

      <div className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">{task.title}</h1>
            {task.jobTitle && <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{task.jobTitle}</p>}
          </div>
          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClass}`}>{task.workflowStatus}</span>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${priorityClass}`}>{task.priority}</span>
            <button
              type="button"
              onClick={() => navigate('/candidate/tasks')}
              className="inline-flex items-center gap-2 rounded-xl border-2 border-blue-200 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50 dark:border-blue-800 dark:text-blue-300 dark:hover:bg-slate-700"
            >
              <IconEye className="h-4 w-4" />
              List view
            </button>
            <button
              type="button"
              onClick={() => navigate('/candidate/tasks', { state: { openSubmitTaskId: task.id } })}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 px-4 py-2 text-sm font-semibold text-white shadow-md hover:from-blue-600 hover:to-cyan-600"
            >
              <IconRefresh className="h-4 w-4" />
              {submission ? 'Update' : 'Submit'}
            </button>
          </div>
        </div>

        <p className="mt-6 text-gray-600 dark:text-gray-300">{task.description}</p>

        <div className="mt-6 space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">Progress</span>
            <span className="font-medium text-gray-900 dark:text-white">{task.progress}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-slate-700">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-500"
              style={{ width: `${Math.min(100, Math.max(0, task.progress))}%` }}
            />
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
          <span className="inline-flex items-center gap-1">
            <IconCalendar className="h-4 w-4" />
            Due: {due.toLocaleDateString()}
          </span>
          {overdue && (
            <span className="rounded-md bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900/40 dark:text-red-200">
              Overdue
            </span>
          )}
          {task.department && <span>Dept: {task.department}</span>}
        </div>

      </div>

      {submission && (
        <div className="rounded-2xl border-2 border-emerald-200/80 bg-gradient-to-br from-emerald-500/10 to-transparent p-6 dark:border-emerald-800/60">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <IconCheckSquare className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            <span className="font-semibold text-emerald-800 dark:text-emerald-200">Submitted</span>
            {submission.status && (
              <span
                className={`ml-auto rounded-full px-3 py-1 text-xs font-medium text-white ${
                  submission.status === 'Approved' ? 'bg-emerald-500' : submission.status === 'Rejected' ? 'bg-red-500' : 'bg-amber-500'
                }`}
              >
                {submission.status}
              </span>
            )}
          </div>
          {submission.githubLink && (
            <a
              href={submission.githubLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
            >
              Repository
              <IconExternal className="h-4 w-4" />
            </a>
          )}
          {submission.feedback && (
            <div className="mt-4 rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-700 shadow-sm dark:border-slate-600 dark:bg-slate-900 dark:text-gray-300">
              <p className="font-semibold text-gray-900 dark:text-white">Feedback</p>
              <pre className="mt-2 whitespace-pre-wrap font-sans">{submission.feedback}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
