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

const RegionalDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [selectedState, setSelectedState] = useState('maharashtra');
  const [data, setData] = useState({
    kpis: { institutions: 20, teachers: 200, students: 5000, score: 83.1 }
  });

  const checkHealth = async () => {
    const online = await checkBackendHealth();
    setIsOnline(online);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/v1/dashboard/regional-admin');
      if (res && res.kpis) {
        setData({
          kpis: {
            institutions: res.kpis.total_institutions,
            teachers: res.kpis.total_teachers,
            students: res.kpis.total_students,
            score: res.kpis.avg_system_score
          }
        });
      }
    } catch (err) {
      console.warn("Failed to load regional dashboard, using mocks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadData();
  }, []);

  // Performance radar chart or risk comparison
  const radarOption = {
    tooltip: {},
    legend: {
      data: ['Comprehension Rate', 'Attendance Rate', 'Pacing Index'],
      textStyle: { color: '#ccc' }
    },
    radar: {
      indicator: [
        { name: 'District North', max: 100 },
        { name: 'District East', max: 100 },
        { name: 'District West', max: 100 },
        { name: 'District South', max: 100 },
        { name: 'District Central', max: 100 }
      ],
      axisName: { color: '#888' },
      splitLine: { lineStyle: { color: '#222' } },
      splitArea: { show: false }
    },
    series: [
      {
        name: 'Regional Metrics',
        type: 'radar',
        data: [
          {
            value: [84, 88, 79, 91, 85],
            name: 'Comprehension Rate',
            itemStyle: { color: '#10b981' }
          }
        ]
      }
    ]
  };

  return (
    <GovernanceLayout level="Regional" healthStatus={isOnline ? "Healthy" : "Offline"}>
      <ExecutiveHeader 
        level="Regional" 
        healthStatus={isOnline ? "Online" : "Offline"}
        onRefresh={() => { checkHealth(); loadData(); }}
        loading={loading}
      />

      <KPIBand>
        <KPICard title="Total Institutions" value={data.kpis.institutions} color="text-orange-400" />
        <KPICard title="Total Active Teachers" value={data.kpis.teachers} color="text-blue-400" />
        <KPICard title="Aggregate Students" value={data.kpis.students} color="text-purple-400" />
        <KPICard title="Average System Score" value={`${data.kpis.score}%`} color="text-green-400" />
        <KPICard title="Redundancy Level" value="Triple Region" color="text-emerald-400" />
        <KPICard title="Survivability Index" value="99.99%" color="text-green-400" />
      </KPIBand>

      <DashboardGrid>
        <DashboardZone cols="lg:col-span-8">
          <WidgetContainer title="Regional Geospatial Nodes" subTitle="Map indicators across region">
            <GeospatialMap selectedState={selectedState} onStateChange={setSelectedState} />
          </WidgetContainer>
        </DashboardZone>

        <DashboardZone cols="lg:col-span-4">
          <WidgetContainer title="Regional Performance Radar" subTitle="Multidimensional district index">
            <EChartsWidget option={radarOption} height="240px" />
          </WidgetContainer>

          <WidgetContainer title="Active Replay Workers">
            <div className="space-y-4 text-xs mt-2">
              <div className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/5">
                <span className="text-gray-400">Worker 1</span>
                <span className="text-emerald-400 font-bold uppercase tracking-wider text-[10px]">Processing (12.4M logs)</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/5">
                <span className="text-gray-400">Worker 2</span>
                <span className="text-emerald-400 font-bold uppercase tracking-wider text-[10px]">Processing (8.9M logs)</span>
              </div>
            </div>
          </WidgetContainer>
        </DashboardZone>
      </DashboardGrid>
    </GovernanceLayout>
  );
};

export default RegionalDashboard;
