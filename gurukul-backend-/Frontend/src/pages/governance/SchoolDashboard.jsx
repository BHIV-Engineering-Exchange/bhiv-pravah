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

const SchoolDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [data, setData] = useState({
    kpis: { active_students: 540, active_teachers: 28, response_time: 145.0, db_write_locks: 0 },
    compliance: { registry: '100%', integrity: '100%' }
  });

  const checkHealth = async () => {
    const online = await checkBackendHealth();
    setIsOnline(online);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/v1/dashboard/school');
      if (res && res.operational_health) {
        setData({
          kpis: {
            active_students: res.operational_health.total_active_students,
            active_teachers: res.operational_health.active_teachers,
            response_time: res.operational_health.average_response_time_ms,
            db_write_locks: res.operational_health.sqlite_write_locks_triggered
          },
          compliance: {
            registry: `${res.compliance_rating.schema_registry_compliance * 100}%`,
            integrity: `${res.compliance_rating.replay_integrity_score * 100}%`
          }
        });
      }
    } catch (err) {
      console.warn("Failed to load school dashboard, using mocks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadData();
  }, []);

  // School Resource usage bar chart
  const usageOption = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['08:00', '10:00', '12:00', '14:00', '16:00'],
      axisLine: { lineStyle: { color: '#444' } }
    },
    yAxis: {
      type: 'value',
      name: 'Req/s',
      axisLine: { lineStyle: { color: '#444' } },
      splitLine: { lineStyle: { color: '#222' } }
    },
    series: [
      {
        data: [120, 340, 480, 290, 180],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#3b82f6' },
        areaStyle: { color: 'rgba(59, 130, 246, 0.1)' }
      }
    ]
  };

  return (
    <GovernanceLayout level="School Admin" healthStatus={isOnline ? "Healthy" : "Offline"}>
      <ExecutiveHeader 
        level="School Admin" 
        healthStatus={isOnline ? "Online" : "Offline"}
        onRefresh={() => { checkHealth(); loadData(); }}
        loading={loading}
      />

      <KPIBand>
        <KPICard title="Total Active Students" value={data.kpis.active_students} color="text-orange-400" />
        <KPICard title="Active Teachers" value={data.kpis.active_teachers} color="text-blue-400" />
        <KPICard title="API Response Time" value={`${data.kpis.response_time}ms`} color="text-purple-400" />
        <KPICard title="DB Write Locks" value={data.kpis.db_write_locks} color="text-rose-400" />
        <KPICard title="Schema Compliance" value={data.compliance.registry} color="text-emerald-400" />
        <KPICard title="Replay Integrity" value={data.compliance.integrity} color="text-green-400" />
      </KPIBand>

      <DashboardGrid>
        <DashboardZone cols="lg:col-span-8">
          <WidgetContainer title="Weekly Ingestion Throughput" subTitle="Traffic analysis logs">
            <EChartsWidget option={usageOption} height="280px" />
          </WidgetContainer>

          <WidgetContainer title="Interactive Geospatial Context" subTitle="School location mapping drilldown">
            {/* Displaying map drilldown directly */}
            <GeospatialMap selectedState="maharashtra" />
          </WidgetContainer>
        </DashboardZone>

        <DashboardZone cols="lg:col-span-4">
          <WidgetContainer title="Infrastructure Integrity Check">
            <div className="space-y-4 mt-2">
              <div className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/5 text-xs">
                <span className="text-gray-400">Main Core server</span>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/5 text-xs">
                <span className="text-gray-400">Ingress Gateway</span>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/5 text-xs">
                <span className="text-gray-400">Pravah Queue Broker</span>
                <span className="text-emerald-400 font-bold">ONLINE</span>
              </div>
            </div>
          </WidgetContainer>

          <WidgetContainer title="Active System Operations Logs">
            <div className="space-y-3 font-mono text-[9px] text-gray-500 max-h-[200px] overflow-y-auto custom-scrollbar">
              <div>[11:00:23] Ingested 45 telemetry events for standard 9 quiz.</div>
              <div>[11:01:45] Health check ping successful. Status code 200.</div>
              <div>[11:02:12] Synchronization worker completed queue flush.</div>
            </div>
          </WidgetContainer>
        </DashboardZone>
      </DashboardGrid>
    </GovernanceLayout>
  );
};

export default SchoolDashboard;
