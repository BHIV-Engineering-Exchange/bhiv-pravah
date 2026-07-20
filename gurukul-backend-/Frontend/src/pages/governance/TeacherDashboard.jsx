import React, { useState, useEffect } from 'react';
import GovernanceLayout from '../../components/governance/GovernanceLayout';
import ExecutiveHeader from '../../components/dashboard/layout/ExecutiveHeader';
import KPIBand from '../../components/dashboard/layout/KPIBand';
import DashboardGrid from '../../components/dashboard/layout/DashboardGrid';
import DashboardZone from '../../components/dashboard/layout/DashboardZone';
import WidgetContainer from '../../components/dashboard/layout/WidgetContainer';
import EChartsWidget from '../../components/dashboard/charts/EChartsWidget';
import KPICard from '../../components/dashboard/KPICard';
import AlertCard from '../../components/dashboard/AlertCard';
import ActionCard from '../../components/dashboard/ActionCard';
import { apiGet, checkBackendHealth } from '../../utils/apiClient';

const TeacherDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [data, setData] = useState({
    kpis: { total_assigned_students: 32, avg_comprehension_score: 84.2, active_students_today: 29, average_pacing: 1.08 },
    open_alerts: [],
    pending_actions: []
  });

  const checkHealth = async () => {
    const online = await checkBackendHealth();
    setIsOnline(online);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/v1/dashboard/teacher');
      if (res && res.classroom_analytics) {
        setData({
          kpis: {
            total_assigned_students: res.classroom_analytics.total_students,
            avg_comprehension_score: res.classroom_analytics.average_comprehension,
            active_students_today: res.classroom_analytics.active_students_today,
            average_pacing: res.classroom_analytics.average_pacing
          },
          open_alerts: res.warning_flags?.map((wf, idx) => ({
            id: `alt-teach-${idx}`,
            type: 'PACING',
            priority: 'HIGH',
            status: 'OPEN',
            created_at: new Date().toISOString(),
            owner_id: wf.student_id,
            details: wf.alert
          })) || [],
          pending_actions: res.recommendation_queue?.map((rq, idx) => ({
            id: `act-teach-${idx}`,
            title: rq.type.replace(/_/g, ' ').toUpperCase(),
            description: rq.reason,
            status: 'Assigned',
            owner_id: rq.student_id,
            created_at: new Date().toISOString()
          })) || []
        });
      } else {
        // Fallback to real DB API
        const dbRes = await apiGet('/api/v1/dashboard/aggregate');
        if (dbRes && dbRes.role === 'teacher') {
          setData({
            kpis: dbRes.kpis || data.kpis,
            open_alerts: dbRes.open_alerts || [],
            pending_actions: dbRes.pending_actions || []
          });
        }
      }
    } catch (err) {
      console.warn("Failed to load teacher dashboard, using mocks:", err);
      // Generate some default mocks if offline
      setData({
        kpis: { total_assigned_students: 32, avg_comprehension_score: 84.2, active_students_today: 29, average_pacing: 1.08 },
        open_alerts: [
          { id: "alt-mock-1", type: "ATTENDANCE", priority: "CRITICAL", status: "OPEN", owner_id: "student-2", created_at: new Date().toISOString() },
          { id: "alt-mock-2", type: "PACING", priority: "LOW", status: "OPEN", owner_id: "student-3", created_at: new Date().toISOString() }
        ],
        pending_actions: [
          { id: "act-mock-1", title: "Comprehension remedial review", description: "Schedule extra time for standard 9 math modules.", status: "In Progress", owner_id: "teacher-1", created_at: new Date().toISOString() }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadData();
  }, []);

  // ECharts Donuts Configuration
  const donutOption = {
    title: {
      text: 'Comprehension split',
      left: 'center',
      textStyle: { color: '#aaa', fontSize: 12 }
    },
    tooltip: { trigger: 'item' },
    series: [
      {
        name: 'Students Ratio',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#1f2937', borderWidth: 2 },
        label: { show: false },
        data: [
          { value: 18, name: 'Above Target (>85%)', itemStyle: { color: '#10b981' } },
          { value: 9, name: 'On Track (70-85%)', itemStyle: { color: '#3b82f6' } },
          { value: 5, name: 'Risk Alert (<70%)', itemStyle: { color: '#f43f5e' } }
        ]
      }
    ]
  };

  // ECharts Pacing Bar Options
  const barOption = {
    xAxis: {
      type: 'category',
      data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
      axisLine: { lineStyle: { color: '#444' } }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#444' } },
      splitLine: { lineStyle: { color: '#222' } }
    },
    series: [
      {
        data: [1.02, 1.05, 1.08, 1.10, 1.08],
        type: 'bar',
        itemStyle: { color: '#f59e0b' }
      }
    ]
  };

  return (
    <GovernanceLayout level="Teacher" healthStatus={isOnline ? "Healthy" : "Offline"}>
      <ExecutiveHeader 
        level="Teacher" 
        healthStatus={isOnline ? "Online" : "Offline"}
        onRefresh={() => { checkHealth(); loadData(); }}
        loading={loading}
      />

      <KPIBand>
        <KPICard title="Total Assigned Students" value={data.kpis.total_assigned_students} color="text-orange-400" />
        <KPICard title="Average Comprehension" value={`${data.kpis.avg_comprehension_score}%`} color="text-green-400" />
        <KPICard title="Active Students Today" value={data.kpis.active_students_today} color="text-blue-400" />
        <KPICard title="Average Pacing Rate" value={`${data.kpis.average_pacing}x`} color="text-purple-400" />
        <KPICard title="Curriculum Coverage" value="92%" color="text-emerald-400" />
        <KPICard title="Remedial Target Queue" value={data.pending_actions.length} color="text-rose-400" />
      </KPIBand>

      <DashboardGrid>
        {/* Left Column: Visual Analytics */}
        <DashboardZone cols="lg:col-span-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <WidgetContainer title="Classroom Comprehension Distribution" subTitle="Student performance metrics split">
              <EChartsWidget option={donutOption} height="260px" />
            </WidgetContainer>
            <WidgetContainer title="Weekly Pacing Index Tracker" subTitle="Class avg progress rates">
              <EChartsWidget option={barOption} height="260px" />
            </WidgetContainer>
          </div>

          <WidgetContainer title="Pacing Recommendations" subTitle="Automated cognitive routing triggers">
            <div className="space-y-3 mt-2">
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 flex justify-between items-center text-xs">
                <div>
                  <span className="font-bold text-white block">Remedial Lesson Scheduling</span>
                  <span className="text-gray-400 block mt-0.5">Assigned to student standard 9 for pronunciation checks.</span>
                </div>
                <span className="px-2 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded font-bold uppercase tracking-wider text-[9px]">Pacing warning</span>
              </div>
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 flex justify-between items-center text-xs">
                <div>
                  <span className="font-bold text-white block">Fast Track Adaptive Content</span>
                  <span className="text-gray-400 block mt-0.5">Promote top standard learners directly to vocabulary module level 4.</span>
                </div>
                <span className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded font-bold uppercase tracking-wider text-[9px]">Optimization</span>
              </div>
            </div>
          </WidgetContainer>
        </DashboardZone>

        {/* Right Column: Alerts & Actions */}
        <DashboardZone cols="lg:col-span-4">
          <WidgetContainer title="Class Anomaly Signal Feed">
            <div className="space-y-3 max-h-[300px] overflow-y-auto custom-scrollbar">
              {data.open_alerts.length === 0 ? (
                <div className="text-center py-6 text-gray-500 text-xs">No active class anomalies.</div>
              ) : (
                data.open_alerts.map(alt => (
                  <AlertCard key={alt.id} alert={alt} userRole="teacher" onStatusUpdate={() => {}} onAssign={() => {}} />
                ))
              )}
            </div>
          </WidgetContainer>

          <WidgetContainer title="Urgent remedial interventions">
            <div className="space-y-3 max-h-[300px] overflow-y-auto custom-scrollbar">
              {data.pending_actions.length === 0 ? (
                <div className="text-center py-6 text-gray-500 text-xs">No pending remedial interventions.</div>
              ) : (
                data.pending_actions.map(act => (
                  <ActionCard key={act.id} action={act} userRole="teacher" onStatusUpdate={() => {}} onAssign={() => {}} />
                ))
              )}
            </div>
          </WidgetContainer>
        </DashboardZone>
      </DashboardGrid>
    </GovernanceLayout>
  );
};

export default TeacherDashboard;
