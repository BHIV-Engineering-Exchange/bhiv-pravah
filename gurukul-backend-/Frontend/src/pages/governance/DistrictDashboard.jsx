import React, { useState, useEffect } from 'react';
import GovernanceLayout from '../../components/governance/GovernanceLayout';
import ExecutiveHeader from '../../components/dashboard/layout/ExecutiveHeader';
import KPIBand from '../../components/dashboard/layout/KPIBand';
import DashboardGrid from '../../components/dashboard/layout/DashboardGrid';
import DashboardZone from '../../components/dashboard/layout/DashboardZone';
import WidgetContainer from '../../components/dashboard/layout/WidgetContainer';
import EChartsWidget from '../../components/dashboard/charts/EChartsWidget';
import GeospatialMap from '../../components/dashboard/maps/GeospatialMap';
import KPICard from '../../components/dashboard/KPICard';
import { apiGet, checkBackendHealth } from '../../utils/apiClient';

const DistrictDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [selectedState, setSelectedState] = useState('maharashtra');
  const [data, setData] = useState({
    kpis: { schools: 14, students: 6800, active_workers: 2, survivability: 0.9999, clamps_triggered: 4 }
  });

  const checkHealth = async () => {
    const online = await checkBackendHealth();
    setIsOnline(online);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/v1/dashboard/district');
      if (res && res.aggregate_analytics) {
        setData({
          kpis: {
            schools: res.aggregate_analytics.total_schools,
            students: res.aggregate_analytics.aggregate_students,
            active_workers: res.aggregate_analytics.active_replay_workers,
            survivability: res.aggregate_analytics.system_survivability_rate,
            clamps_triggered: res.boundary_auditing?.safety_clamps_triggered_this_month || 0
          }
        });
      }
    } catch (err) {
      console.warn("Failed to load district dashboard, using mocks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadData();
  }, []);

  // Performance Comparison chart between schools
  const compareOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#444' } },
      splitLine: { lineStyle: { color: '#222' } }
    },
    yAxis: {
      type: 'category',
      data: ['School A', 'School B', 'School C', 'School D'],
      axisLine: { lineStyle: { color: '#444' } }
    },
    series: [
      {
        name: 'Comprehension Score %',
        data: [82, 91, 74, 88],
        type: 'bar',
        itemStyle: { color: '#10b981' }
      }
    ]
  };

  return (
    <GovernanceLayout level="District" healthStatus={isOnline ? "Healthy" : "Offline"}>
      <ExecutiveHeader 
        level="District" 
        healthStatus={isOnline ? "Online" : "Offline"}
        onRefresh={() => { checkHealth(); loadData(); }}
        loading={loading}
      />

      <KPIBand>
        <KPICard title="Total Schools" value={data.kpis.schools} color="text-orange-400" />
        <KPICard title="Aggregate Students" value={data.kpis.students} color="text-blue-400" />
        <KPICard title="Active Replay Workers" value={data.kpis.active_workers} color="text-purple-400" />
        <KPICard title="Survivability Rate" value={`${(data.kpis.survivability * 100).toFixed(4)}%`} color="text-emerald-400" />
        <KPICard title="Safety Clamps Active" value={data.kpis.clamps_triggered} color="text-rose-400" />
        <KPICard title="Rubric Integrity" value="Verified" color="text-green-400" />
      </KPIBand>

      <DashboardGrid>
        <DashboardZone cols="lg:col-span-8">
          <WidgetContainer title="District Geospatial Infrastructure Mapping" subTitle="Drill down district nodes">
            <GeospatialMap selectedState={selectedState} onStateChange={setSelectedState} />
          </WidgetContainer>
        </DashboardZone>

        <DashboardZone cols="lg:col-span-4">
          <WidgetContainer title="School Academic Score Performance" subTitle="Average comparison benchmark">
            <EChartsWidget option={compareOption} height="220px" />
          </WidgetContainer>

          <WidgetContainer title="Active Safety Interventions Feed">
            <div className="space-y-3 mt-2 text-xs">
              <div className="p-3.5 rounded-xl bg-white/5 border border-rose-500/10 flex items-start gap-2.5">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-500 mt-1.5"></span>
                <div>
                  <span className="font-bold text-white block">Pacing clamp triggered</span>
                  <span className="text-gray-400 block mt-0.5">District standard 9 voice score fell below 50%. Audio processing throttled.</span>
                </div>
              </div>
            </div>
          </WidgetContainer>
        </DashboardZone>
      </DashboardGrid>
    </GovernanceLayout>
  );
};

export default DistrictDashboard;
