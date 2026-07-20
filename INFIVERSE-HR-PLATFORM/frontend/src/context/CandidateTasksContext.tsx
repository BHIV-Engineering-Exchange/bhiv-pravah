import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { CandidateTaskSubmission, CandidateWorkflowTask } from '../pages/candidate/candidateTasksTypes'

type CandidateTasksContextValue = {
  tasks: CandidateWorkflowTask[]
  setTasks: React.Dispatch<React.SetStateAction<CandidateWorkflowTask[]>>
  getTaskById: (id: string) => CandidateWorkflowTask | undefined
  upsertSubmission: (taskId: string, submission: CandidateTaskSubmission) => void
}

const CandidateTasksContext = createContext<CandidateTasksContextValue | null>(null)

export function CandidateTasksProvider({ children }: { children: ReactNode }) {
  const [tasks, setTasks] = useState<CandidateWorkflowTask[]>([])

  const getTaskById = useCallback(
    (id: string) => tasks.find((t) => t.id === id),
    [tasks]
  )

  const upsertSubmission = useCallback((taskId: string, submission: CandidateTaskSubmission) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId
          ? {
              ...t,
              submission,
              workflowStatus: t.workflowStatus === 'Pending' ? 'In Progress' : t.workflowStatus,
            }
          : t
      )
    )
  }, [])

  const value = useMemo(
    () => ({
      tasks,
      setTasks,
      getTaskById,
      upsertSubmission,
    }),
    [tasks, getTaskById, upsertSubmission]
  )

  return <CandidateTasksContext.Provider value={value}>{children}</CandidateTasksContext.Provider>
}

export function useCandidateTasks() {
  const ctx = useContext(CandidateTasksContext)
  if (!ctx) {
    throw new Error('useCandidateTasks must be used within CandidateTasksProvider')
  }
  return ctx
}
