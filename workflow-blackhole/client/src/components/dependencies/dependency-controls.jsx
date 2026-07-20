import { Button } from "../ui/button"
import { Input } from "../ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select"
import { Tabs, TabsList, TabsTrigger } from "../ui/tabs"
import { Search, ZoomIn, ZoomOut, RefreshCw, Filter } from "lucide-react"

export function DependencyControls() {
  return (
    <div className="flex flex-col gap-4">
      {/* Top Row: Search and Filters */}
      <div className="flex flex-col md:flex-row gap-3 items-start md:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center flex-1 w-full">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              type="search" 
              placeholder="Search tasks..." 
              className="w-full pl-10 h-11 rounded-xl border-2 font-medium"
            />
          </div>

          <Select>
            <SelectTrigger className="w-full sm:w-48 h-11 rounded-xl border-2 font-medium">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Department" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="all" className="font-medium">All Departments</SelectItem>
              <SelectItem value="marketing" className="font-medium">Marketing</SelectItem>
              <SelectItem value="sales" className="font-medium">Sales</SelectItem>
              <SelectItem value="operations" className="font-medium">Operations</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* View Controls */}
        <div className="flex items-center gap-2 w-full md:w-auto">
          <Tabs defaultValue="graph" className="flex-1 md:flex-none">
            <TabsList className="grid w-full grid-cols-2 h-11">
              <TabsTrigger value="graph" className="font-semibold rounded-lg">Graph</TabsTrigger>
              <TabsTrigger value="gantt" className="font-semibold rounded-lg">Gantt</TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="flex items-center gap-1.5 bg-muted/50 rounded-xl p-1">
            <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg hover:bg-background transition-colors">
              <ZoomIn className="h-4 w-4" />
              <span className="sr-only">Zoom In</span>
            </Button>
            <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg hover:bg-background transition-colors">
              <ZoomOut className="h-4 w-4" />
              <span className="sr-only">Zoom Out</span>
            </Button>
            <Button variant="ghost" size="icon" className="h-9 w-9 rounded-lg hover:bg-background transition-colors">
              <RefreshCw className="h-4 w-4" />
              <span className="sr-only">Refresh</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
