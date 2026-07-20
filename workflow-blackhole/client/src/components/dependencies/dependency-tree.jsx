"use client"

import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"
import { Loader2 } from "lucide-react"
import { api } from "../../lib/api"
import { useToast } from "../../hooks/use-toast"
import { useIsMobile } from "../../hooks/use-mobile"

// Utility function to map status to color
const getStatusColor = (status) => {
  const colorMap = {
    "Pending": "#f59e0b",
    "In Progress": "#3b82f6",
    "Completed": "#22c55e",
  }
  return colorMap[status] || "#64748b"
}

export function DependencyTree() {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [tasks, setTasks] = useState([])
  const [departments, setDepartments] = useState([])
  const [selectedDepartment, setSelectedDepartment] = useState("All")
  const isMobile = useIsMobile()

  // Fetch tasks and departments
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        const [tasksData, departmentsResponse] = await Promise.all([
          api.tasks.getTasks(),
          api.departments.getDepartments(),
        ])

        const departmentsData = departmentsResponse.success ? departmentsResponse.data : departmentsResponse

        setTasks(tasksData)
        setDepartments(Array.isArray(departmentsData) ? departmentsData : [])
        setError(null)
      } catch (err) {
        setError(err.message || "Failed to load data")
        toast({
          title: "Error",
          description: err.message || "Failed to load tasks and departments",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [toast])

  // Filter tasks by selected department
  const filteredTasks =
    selectedDepartment === "All" ? tasks : tasks.filter((task) => task.department?.name === selectedDepartment)

  // Responsive sizing for the SVG
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current && svgRef.current) {
        const containerWidth = containerRef.current.clientWidth
        const containerHeight = Math.max(500, window.innerHeight * 0.7)

        d3.select(svgRef.current).attr("width", containerWidth).attr("height", containerHeight)

        renderHierarchicalTree()
      }
    }

    window.addEventListener("resize", updateSize)
    updateSize()

    return () => window.removeEventListener("resize", updateSize)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [containerRef, svgRef, filteredTasks, departments])

  // Build hierarchical data structure
  const buildHierarchy = () => {
    if (!filteredTasks.length) return null

    // Create a map of task IDs to tasks
    const taskMap = new Map()
    filteredTasks.forEach((task) => {
      taskMap.set(task._id, {
        id: task._id,
        title: task.title,
        status: task.status,
        department: task.department?.name || "Unknown",
        dependencies: task.dependencies?.map((d) => d._id) || [],
        children: [],
      })
    })

    // Find root tasks (tasks with no dependencies or dependencies outside filtered set)
    const rootTasks = []
    const childTaskIds = new Set()

    filteredTasks.forEach((task) => {
      const deps = task.dependencies?.map((d) => d._id) || []
      const validDeps = deps.filter((depId) => taskMap.has(depId))

      if (validDeps.length === 0) {
        rootTasks.push(taskMap.get(task._id))
      } else {
        validDeps.forEach((depId) => {
          const depTask = taskMap.get(depId)
          if (depTask && !depTask.children.some((c) => c.id === task._id)) {
            depTask.children.push(taskMap.get(task._id))
            childTaskIds.add(task._id)
          }
        })
      }
    })

    // If no clear hierarchy, create a virtual root
    if (rootTasks.length === 0) {
      return {
        id: "root",
        title: "All Tasks",
        status: "",
        department: "",
        children: Array.from(taskMap.values()),
      }
    } else if (rootTasks.length === 1) {
      return rootTasks[0]
    } else {
      return {
        id: "root",
        title: "Project Tasks",
        status: "",
        department: "",
        children: rootTasks,
      }
    }
  }

  // Render Hierarchical Tree
  const renderHierarchicalTree = () => {
    if (!svgRef.current || !filteredTasks.length) return

    const hierarchy = buildHierarchy()
    if (!hierarchy) return

    d3.select(svgRef.current).selectAll("*").remove()

    const svg = d3.select(svgRef.current)
    const width = +svg.attr("width")
    const height = +svg.attr("height")
    const margin = { top: 40, right: 120, bottom: 40, left: 120 }

    svg.style("background", "#f9fafb")

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`)

    // Create tooltip
    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "tree-tooltip")
      .style("position", "absolute")
      .style("background", "#fff")
      .style("padding", "8px 12px")
      .style("border", "1px solid #ccc")
      .style("border-radius", "6px")
      .style("pointer-events", "none")
      .style("opacity", 0)
      .style("z-index", 1000)
      .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")

    // Create tree layout
    const treeLayout = d3.tree().size([height - margin.top - margin.bottom, width - margin.left - margin.right])

    const root = d3.hierarchy(hierarchy)
    treeLayout(root)

    // Add links
    g.append("g")
      .selectAll("path")
      .data(root.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr("fill", "none")
      .attr("stroke", "#cbd5e1")
      .attr("stroke-width", 2)
      .attr(
        "d",
        d3
          .linkHorizontal()
          .x((d) => d.y)
          .y((d) => d.x),
      )

    // Add nodes
    const node = g
      .append("g")
      .selectAll("g")
      .data(root.descendants())
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", (d) => `translate(${d.y},${d.x})`)

    // Add circles
    node
      .append("circle")
      .attr("r", isMobile ? 6 : 8)
      .attr("fill", (d) => (d.data.status ? getStatusColor(d.data.status) : "#94a3b8"))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .style("cursor", "pointer")
      .on("mouseover", function (event, d) {
        d3.select(this).attr("r", isMobile ? 8 : 10).attr("stroke-width", 3)

        if (d.data.title && d.data.title !== "All Tasks" && d.data.title !== "Project Tasks") {
          tooltip
            .style("opacity", 1)
            .html(
              `<div style="font-size: 13px;">
                <strong>${d.data.title}</strong><br/>
                <span style="color: #64748b;">Department: ${d.data.department}</span><br/>
                <span style="color: ${getStatusColor(d.data.status)};">Status: ${d.data.status}</span>
                ${d.data.children && d.data.children.length > 0 ? `<br/><span style="color: #64748b;">Children: ${d.data.children.length}</span>` : ""}
              </div>`,
            )
            .style("left", `${event.pageX + 15}px`)
            .style("top", `${event.pageY - 15}px`)
        }
      })
      .on("mouseout", function () {
        d3.select(this).attr("r", isMobile ? 6 : 8).attr("stroke-width", 2)
        tooltip.style("opacity", 0)
      })

    // Add labels
    node
      .append("text")
      .attr("dy", "0.31em")
      .attr("x", (d) => (d.children ? -12 : 12))
      .attr("text-anchor", (d) => (d.children ? "end" : "start"))
      .text((d) => {
        if (isMobile) {
          return d.data.title.length > 15 ? d.data.title.substring(0, 15) + "..." : d.data.title
        }
        return d.data.title.length > 25 ? d.data.title.substring(0, 25) + "..." : d.data.title
      })
      .style("font-size", isMobile ? "10px" : "12px")
      .style("fill", "#1e293b")
      .style("font-weight", "500")
      .clone(true)
      .lower()
      .attr("stroke", "white")
      .attr("stroke-width", 3)

    // Add zoom behavior
    const zoom = d3
      .zoom()
      .scaleExtent([0.5, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform)
      })

    svg.call(zoom)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[500px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[500px]">
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Department Filter */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium">Filter by Department:</label>
        <select
          value={selectedDepartment}
          onChange={(e) => setSelectedDepartment(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm bg-background"
        >
          <option value="All">All Departments</option>
          {departments.map((dept) => (
            <option key={dept._id} value={dept.name}>
              {dept.name}
            </option>
          ))}
        </select>
      </div>

      {/* Tree Container */}
      <div ref={containerRef} className="w-full overflow-hidden rounded-lg border bg-white">
        <svg ref={svgRef} className="w-full"></svg>
      </div>

      {/* Instructions */}
      <div className="text-xs text-muted-foreground">
        <p>💡 Hover over nodes to see details • Scroll to zoom • Drag to pan</p>
      </div>
    </div>
  )
}
