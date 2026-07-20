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

const StateDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [selectedState, setSelectedState] = useState('maharashtra');
  const [data, setData] = useState({
    kpis: { districts: 11, active_sessions: 18450, onboarding_rate: 0.94, alignment_rate: 1.0 },
    governance: { curriculums: ["National Language Core v4", "Stem Science v2"], audit_hash: "2f6c91a0b3f88d9294e0e227" }
  });

  const checkHealth = async () => {
    const online = await checkBackendHealth();
    setIsOnline(online);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/v1/dashboard/state');
      if (res && res.statewide_metrics) {
        setData({
          kpis: {
            districts: res.statewide_metrics.total_districts,
            active_sessions: res.statewide_metrics.active_sessions_hourly,
            onboarding_rate: res.statewide_metrics.teacher_onboarding_rate,
            alignment_rate: res.statewide_metrics.national_standards_alignment
          },
          governance: {
            curriculums: res.governance?.approved_curriculums || [],
            audit_hash: res.governance?.audit_trail_hash || ""
          }
        });
      }
    } catch (err) {
      console.warn("Failed to load state dashboard, using mocks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadData();
  }, []);

  // Statewide sessions hourly progress line chart
  const sessionsOption = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00'],
      axisLine: { lineStyle: { color: '#444' } }
    },
    yAxis: {
      type: 'value',
      name: 'Sessions',
      axisLine: { lineStyle: { color: '#444' } },
      splitLine: { lineStyle: { color: '#222' } }
    },
    series: [
      {
        name: 'Active Sessions',
        data: [12000, 15400, 18450, 19200, 14000, 17800, 18600],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#f59e0b' },
        areaStyle: { color: 'rgba(245, 158, 11, 0.1)' }
      }
    ]
  };

  return (
    <GovernanceLayout level="State" healthStatus={isOnline ? "Healthy" : "Offline"}>
      <ExecutiveHeader 
        level="State" 
        healthStatus={isOnline ? "Online" : "Offline"}
        onRefresh={() => { checkHealth(); loadData(); }}
        loading={loading}
      />

      <KPIBand>
        <KPICard title="Total Statewide Districts" value={data.kpis.districts} color="text-orange-400" />
        <KPICard title="Hourly Active Sessions" value={data.kpis.active_sessions.toLocaleString()} color="text-blue-400" />
        <KPICard title="Teacher Onboarding Rate" value={`${(data.kpis.onboarding_rate * 100).toFixed(0)}%`} color="text-purple-400" />
        <KPICard title="National Standard Align" value={`${(data.kpis.alignment_rate * 100).toFixed(0)}%`} color="text-emerald-400" />
        <KPICard title="Statewide Coverage" value="96%" color="text-green-400" />
        <KPICard title="Total Analytics Collected" value="1.8M" color="text-amber-400" />
      </KPIBand>

      <DashboardGrid>
        <DashboardZone cols="lg:col-span-8">
          <WidgetContainer title="Statewide Operational Geospatial Drilling" subTitle="Filter and drilldown between Maharashtra and MP district boundaries">
            <GeospatialMap selectedState={selectedState} onStateChange={setSelectedState} />
          </WidgetContainer>
        </DashboardZone>

        <DashboardZone cols="lg:col-span-4">
          <WidgetContainer title="Statewide Hourly Sessions Stream" subTitle="Active session count hourly progression">
            <EChartsWidget option={sessionsOption} height="220px" />
          </WidgetContainer>

          <WidgetContainer title="Approved Statewide Curriculums">
            <div className="space-y-2.5 mt-1 text-xs">
              {data.governance.curriculums.map((curr, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-white/5 border border-white/5 font-medium text-white">
                  {curr}
                </div>
              ))}
              <div className="pt-2">
                <span className="text-[10px] text-gray-500 block uppercase">Audit Trail Hash</span>
                <span className="font-mono text-[10px] text-gray-400 break-all select-all block mt-0.5">{data.governance.audit_hash}</span>
              </div>
            </div>
          </WidgetContainer>
        </DashboardZone>
      </DashboardGrid>
    </GovernanceLayout>
  );
};

export default StateDashboard;
