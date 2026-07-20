import { useEffect, useState } from "react";
import { useSocket } from "../../context/socket-context";
import { useAuth } from "../../context/auth-context";
import { Alert, AlertDescription, AlertTitle } from "../ui/alert";
import { AlertCircle, X } from "lucide-react";
import { Button } from "../ui/button";

export function ProcurementAlerts() {
  const { socket } = useSocket();
  const { user } = useAuth();
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    if (!socket || !user || user.role !== 'Admin') return;

    const handleLowTaskAlert = (data) => {
      if (data.adminId === user.id) {
        const newAlert = {
          id: Date.now(),
          count: data.count,
          employees: data.employees,
          timestamp: new Date()
        };
        setAlerts(prev => [newAlert, ...prev.slice(0, 4)]); // Keep only 5 most recent
      }
    };

    socket.on('procurement:low-task-alert', handleLowTaskAlert);

    return () => {
      socket.off('procurement:low-task-alert', handleLowTaskAlert);
    };
  }, [socket, user]);

  const dismissAlert = (alertId) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  if (alerts.length === 0) return null;

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <Alert key={alert.id} className="bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-900">
          <AlertCircle className="h-4 w-4" />
          <div className="flex-1">
            <AlertTitle className="flex items-center justify-between">
              Procurement Alert
              <Button
                variant="ghost"
                size="sm"
                onClick={() => dismissAlert(alert.id)}
                className="h-6 w-6 p-0"
              >
                <X className="h-3 w-3" />
              </Button>
            </AlertTitle>
            <AlertDescription>
              {alert.count} employees have less than 1 active task:
              <div className="mt-1 text-sm">
                {alert.employees.map((emp, idx) => (
                  <span key={idx}>
                    {emp.name} ({emp.activeTasks} tasks)
                    {idx < alert.employees.length - 1 ? ', ' : ''}
                  </span>
                ))}
              </div>
            </AlertDescription>
          </div>
        </Alert>
      ))}
    </div>
  );
}