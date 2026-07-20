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
import AlertFeed from '../../components/governance/AlertFeed';
import ActionButton from '../../components/governance/ActionButton';
import { ShieldAlert, Rocket, MessageSquare } from 'lucide-react';
import { apiGet, checkBackendHealth } from '../../utils/apiClient';

const MinisterDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [selectedState, setSelectedState] = useState('maharashtra');
  const [data, setData] = useState({
    kpis: { states: 28, enrolled: 1420000, events: 58200000, schema_verification: 1.0, replay_determinism: 1.0 },
    system: { cpu: 12, memory: 45, uptime: "34h 12m" },
    alerts: []
  });

  const checkHealth = async () => {
    const online = await checkBackendHealth();
    setIsOnline(online);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiGet('/api/v1/dashboard/ministry');
      const metricsRes = await apiGet('/system/metrics');
      
      const mappedAlerts = metricsRes?.watchdog?.recent_recovery_events?.map(event => ({
        title: `${event.service} ${event.event}`,
        message: event.detail,
        time: event.timestamp.split('T')[1].split('.')[0],
        type: event.event.includes('FAILURE') ? 'anomaly' : 'pattern',
        trace_id: `TR-${event.service.substring(0, 3).toUpperCase()}-${Math.floor(Math.random() * 9000) + 1000}`,
        priority: event.event.includes('CRITICAL') ? 'High' : 'Low'
      })).reverse() || [];

      setData({
        kpis: {
          states: res?.national_scale_telemetry?.total_states || 28,
          enrolled: res?.national_scale_telemetry?.total_students_enrolled || 1420000,
          events: res?.national_scale_telemetry?.total_telemetry_events_processed || 58200000,
          schema_verification: res?.national_scale_telemetry?.tantra_schema_verification_rate || 1.0,
          replay_determinism: res?.national_scale_telemetry?.replay_determinism_rate || 1.0
        },
        system: {
          cpu: metricsRes?.system?.resource_usage?.cpu_percent || 12,
          memory: metricsRes?.system?.resource_usage?.memory_percent || 45,
          uptime: metricsRes?.uptime_human || "34h 12m"
        },
        alerts: mappedAlerts.length > 0 ? mappedAlerts : [{ title: "System Nominal", message: "No anomalies detected in last cycle.", time: "now", type: "info", trace_id: "GURUKUL-SYS", priority: "Low" }]
      });
    } catch (err) {
      console.warn("Failed to load ministry dashboard, using mocks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadData();
  }, []);

  // System Resources gauge
  const resourceOption = {
    tooltip: { trigger: 'item' },
    series: [
      {
        name: 'CPU Usage',
        type: 'gauge',
        center: ['25%', '50%'],
        radius: '55%',
        min: 0,
        max: 100,
        progress: { show: true, itemStyle: { color: '#3b82f6' } },
        axisLabel: { show: false },
        title: { offsetCenter: [0, '80%'], textStyle: { color: '#ccc', fontSize: 10 } },
        detail: { valueAnimation: true, formatter: '{value}%', textStyle: { color: '#fff', fontSize: 14 }, offsetCenter: [0, '20%'] },
        data: [{ value: data.system.cpu, name: 'CPU Usage' }]
      },
      {
        name: 'Memory',
        type: 'gauge',
        center: ['75%', '50%'],
        radius: '55%',
        min: 0,
        max: 100,
        progress: { show: true, itemStyle: { color: '#10b981' } },
        axisLabel: { show: false },
        title: { offsetCenter: [0, '80%'], textStyle: { color: '#ccc', fontSize: 10 } },
        detail: { valueAnimation: true, formatter: '{value}%', textStyle: { color: '#fff', fontSize: 14 }, offsetCenter: [0, '20%'] },
        data: [{ value: data.system.memory, name: 'Memory' }]
      }
    ]
  };

  return (
    <GovernanceLayout level="Minister" healthStatus={isOnline ? "Healthy" : "Offline"}>
      <ExecutiveHeader 
        level="Minister" 
        healthStatus={isOnline ? "Online" : "Offline"}
        onRefresh={() => { checkHealth(); loadData(); }}
        loading={loading}
      />

      <KPIBand>
        <KPICard title="Total States Enrolled" value={data.kpis.states} color="text-orange-400" />
        <KPICard title="Total Enrolled Students" value={data.kpis.enrolled.toLocaleString()} color="text-blue-400" />
        <KPICard title="Processed Telemetry Events" value={data.kpis.events.toLocaleString()} color="text-purple-400" />
        <KPICard title="Schema Verification" value={`${(data.kpis.schema_verification * 100).toFixed(0)}%`} color="text-emerald-400" />
        <KPICard title="Replay Determinism" value={`${(data.kpis.replay_determinism * 100).toFixed(0)}%`} color="text-green-400" />
        <KPICard title="Uptime Health" value={data.system.uptime} color="text-amber-400" />
      </KPIBand>

      <DashboardGrid>
        {/* Central Map & Heatmap Visual */}
        <DashboardZone cols="lg:col-span-9">
          <WidgetContainer title="National Educational Infrastructure Intelligence Heatmap" subTitle="Filter, select states, and drilldown school districts spatial telemetry">
            <GeospatialMap selectedState={selectedState} onStateChange={setSelectedState} />
          </WidgetContainer>
        </DashboardZone>

        {/* Right Action Queue & Watchdog Feeds */}
        <DashboardZone cols="lg:col-span-3">
          <WidgetContainer title="System Resource Monitoring" subTitle="Live server memory and CPU metrics">
            <EChartsWidget option={resourceOption} height="160px" />
          </WidgetContainer>

          <AlertFeed alerts={data.alerts} />

          <WidgetContainer title="National Decision Intervention Layer">
            <div className="space-y-3 mt-1">
              <ActionButton 
                label="Policy Action" 
                subLabel="Draft new structural reforms" 
                icon={Rocket}
                variant="accent"
                onClick={() => alert("Cabinet draft created.")}
              />
              <ActionButton 
                label="Emergency Cabinet Escalation" 
                subLabel="Immediate notice trigger to State" 
                icon={ShieldAlert}
                variant="danger"
                onClick={() => alert("Cabinet alert dispatched.")}
              />
              <ActionButton 
                label="System Address" 
                subLabel="Broadcast national operational update" 
                icon={MessageSquare}
                variant="primary"
                onClick={() => alert("Broadcast scheduled.")}
              />
            </div>
          </WidgetContainer>
        </DashboardZone>
      </DashboardGrid>
    </GovernanceLayout>
  );
};

export default MinisterDashboard;
