import { useState } from "react"
import { DependencyGraph } from "../components/dependencies/dependency-graph"
import { DependencyGantt } from "../components/dependencies/dependency-gantt"
import { DependencySwimlane } from "../components/dependencies/dependency-swimlane"
import { Network, Calendar, Layers } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs"

function Dependencies() {
  const [activeTab, setActiveTab] = useState("network")

  return (
    <div className="space-y-6 pb-8">
      {/* Header Section - Settings Style */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-purple-500/10 dark:bg-purple-500/20 flex items-center justify-center">
            <Network className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Task Dependencies</h1>
            <p className="text-muted-foreground">Visualize and manage task dependencies across departments</p>
          </div>
        </div>
      </div>

      {/* Graph Container with Tabs */}
      <div className="border-2 rounded-xl p-4 md:p-6 bg-card shadow-xl min-h-[600px] flex flex-col">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-3 mb-6">
            <TabsTrigger value="network" className="flex items-center gap-2">
              <Network className="h-4 w-4" />
              <span className="hidden sm:inline">Network</span>
            </TabsTrigger>
            <TabsTrigger value="gantt" className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span className="hidden sm:inline">Gantt</span>
            </TabsTrigger>
            <TabsTrigger value="swimlane" className="flex items-center gap-2">
              <Layers className="h-4 w-4" />
              <span className="hidden sm:inline">Swimlane</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="network" className="mt-0">
            <DependencyGraph />
          </TabsContent>

          <TabsContent value="gantt" className="mt-0">
            <DependencyGantt />
          </TabsContent>

          <TabsContent value="swimlane" className="mt-0">
            <DependencySwimlane />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default Dependencies
