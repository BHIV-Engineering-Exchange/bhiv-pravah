import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { api } from "../lib/api";
import { Button } from "../components/ui/button";
import { Bell, Calendar, Mail, Send, FileText, Clock, X, CheckCircle, Users, Plus } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { format } from "date-fns";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Checkbox } from "../components/ui/checkbox";

export default function EMSDashboard() {
  const [stats, setStats] = useState({
    totalScheduled: 0,
    sentToday: 0,
    pending: 0,
  });
  const [templates, setTemplates] = useState([]);
  const [scheduledEmails, setScheduledEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [loadingScheduled, setLoadingScheduled] = useState(true);
  
  // Custom email dialog state
  const [isEmailDialogOpen, setIsEmailDialogOpen] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [emailForm, setEmailForm] = useState({
    subject: "",
    message: "",
    scheduleDate: "",
    scheduleTime: "",
  });

  useEffect(() => {
    fetchStats();
    fetchTemplates();
    fetchScheduledEmails();
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await api.users.getUsers();
      const employeeList = Array.isArray(response) ? response : [];
      setEmployees(employeeList.filter(user => user.role !== 'Admin'));
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.ems.getStats();
      if (response.success) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching EMS stats:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      setLoadingTemplates(true);
      const response = await api.ems.getTemplates();
      if (response.success) {
        setTemplates(response.templates || []);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const fetchScheduledEmails = async () => {
    try {
      setLoadingScheduled(true);
      const response = await api.ems.getScheduledEmails();
      if (response.success) {
        setScheduledEmails(response.emails || []);
      }
    } catch (error) {
      console.error('Error fetching scheduled emails:', error);
    } finally {
      setLoadingScheduled(false);
    }
  };

  const handleCancelScheduledEmail = async (emailId) => {
    try {
      const response = await api.ems.cancelScheduledEmail(emailId);
      if (response.success) {
        setSuccess("Scheduled email cancelled successfully!");
        fetchScheduledEmails();
        fetchStats();
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (error) {
      setError(error.message || "Failed to cancel scheduled email");
      setTimeout(() => setError(null), 3000);
    }
  };

  const handleSelectAllEmployees = (checked) => {
    setSelectAll(checked);
    if (checked) {
      setSelectedEmployees(employees.map(emp => emp.email));
    } else {
      setSelectedEmployees([]);
    }
  };

  const handleEmployeeToggle = (email) => {
    setSelectedEmployees(prev => {
      if (prev.includes(email)) {
        return prev.filter(e => e !== email);
      } else {
        return [...prev, email];
      }
    });
  };

  const handleTemplateSelect = (templateId) => {
    setSelectedTemplate(templateId);
    
    // Find the template and populate the form
    const template = templates.find(t => t.templateId === templateId);
    if (template) {
      setEmailForm(prev => ({
        ...prev,
        subject: template.subject.replace(/\{.*?\}/g, '...'), // Remove placeholders
        message: template.htmlBody
          ? template.htmlBody.replace(/<[^>]*>/g, '').replace(/\{.*?\}/g, '...').trim()
          : prev.message
      }));
    }
  };

  const handleClearTemplate = () => {
    setSelectedTemplate("");
    setEmailForm(prev => ({
      ...prev,
      subject: "",
      message: ""
    }));
  };

  const handleSendCustomEmail = async () => {
    if (!emailForm.subject || !emailForm.message) {
      setError("Subject and message are required");
      setTimeout(() => setError(null), 3000);
      return;
    }

    if (selectedEmployees.length === 0) {
      setError("Please select at least one employee");
      setTimeout(() => setError(null), 3000);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      let scheduleTime = null;
      if (emailForm.scheduleDate && emailForm.scheduleTime) {
        scheduleTime = new Date(`${emailForm.scheduleDate}T${emailForm.scheduleTime}`).toISOString();
      }

      const htmlBody = `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #333;">${emailForm.subject}</h2>
          <div style="padding: 20px; background-color: #f5f5f5; border-radius: 8px;">
            <p style="color: #555; line-height: 1.6;">${emailForm.message.replace(/\n/g, '<br>')}</p>
          </div>
          <p style="color: #888; font-size: 12px; margin-top: 20px;">
            This is an automated message from the Workflow Management System.
          </p>
        </div>
      `;

      const response = await api.post('/ems/send-custom-email', {
        recipients: selectedEmployees,
        subject: emailForm.subject,
        htmlBody: htmlBody,
        scheduleTime: scheduleTime
      });

      if (response.success) {
        setSuccess(scheduleTime ? "Email scheduled successfully!" : "Email sent successfully!");
        setIsEmailDialogOpen(false);
        setEmailForm({
          subject: "",
          message: "",
          scheduleDate: "",
          scheduleTime: "",
        });
        setSelectedEmployees([]);
        setSelectAll(false);
        setSelectedTemplate("");
        fetchStats();
        fetchScheduledEmails();
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (error) {
      setError(error.message || "Failed to send email");
      setTimeout(() => setError(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleSendTaskReminders = async () => {
    setLoading(true);
    setSuccess(null);
    setError(null);

    try {
      const response = await api.ems.sendTaskReminders({
        reminderType: "due_soon"
      });

      if (response.success) {
        setSuccess("Task reminders sent successfully!");
        fetchStats(); // Refresh stats
      }
    } catch (error) {
      setError(error.message || "Failed to send task reminders");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">EMS Dashboard</h1>
          <p className="text-muted-foreground">
            Manage automated email notifications and communications
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setIsEmailDialogOpen(true)}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Send Custom Email
          </Button>
          <Button
            onClick={handleSendTaskReminders}
            disabled={loading}
            className="bg-primary hover:bg-primary/90"
          >
            <Send className="h-4 w-4 mr-2" />
            Send Task Reminders
          </Button>
        </div>
      </div>

      {success && (
        <Alert className="bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-900">
          <Bell className="h-4 w-4" />
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-900">
          <Bell className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled Emails</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalScheduled}</div>
            <p className="text-xs text-muted-foreground">
              Total emails scheduled for delivery
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sent Today</CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.sentToday}</div>
            <p className="text-xs text-muted-foreground">
              Emails sent in the last 24 hours
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Delivery</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pending}</div>
            <p className="text-xs text-muted-foreground">
              Emails queued for sending
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Email Templates Section */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Email Templates
          </CardTitle>
          <CardDescription>
            Manage and customize email templates for different notifications
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingTemplates ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading templates...
            </div>
          ) : templates.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No email templates found
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {templates.map((template) => (
                <Card key={template._id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center justify-between">
                      <span className="truncate">{template.name}</span>
                      <Badge variant="outline" className="ml-2 shrink-0">
                        {template.category}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {template.subject}
                    </p>
                    <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                      <Mail className="h-3 w-3" />
                      <span>Template ID: {template.templateId}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scheduled Emails Section */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Scheduled Emails
          </CardTitle>
          <CardDescription>
            View and manage upcoming scheduled email communications
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingScheduled ? (
            <div className="text-center py-8 text-muted-foreground">
              Loading scheduled emails...
            </div>
          ) : scheduledEmails.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No scheduled emails found
            </div>
          ) : (
            <div className="space-y-3">
              {scheduledEmails.map((email) => (
                <Card key={email._id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-sm">{email.subject}</h4>
                          <Badge 
                            variant={email.status === 'scheduled' ? 'default' : email.status === 'sent' ? 'success' : 'destructive'}
                            className="text-xs"
                          >
                            {email.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>
                              {email.scheduledTime 
                                ? format(new Date(email.scheduledTime), 'PPpp')
                                : 'Not scheduled'}
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            <span>{email.recipients?.length || 0} recipient(s)</span>
                          </div>
                        </div>
                        {email.status === 'sent' && email.sentAt && (
                          <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                            <CheckCircle className="h-3 w-3" />
                            <span>Sent: {format(new Date(email.sentAt), 'PPpp')}</span>
                          </div>
                        )}
                      </div>
                      {email.status === 'scheduled' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCancelScheduledEmail(email._id)}
                          className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Custom Email Dialog */}
      <Dialog open={isEmailDialogOpen} onOpenChange={setIsEmailDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Send Custom Email
            </DialogTitle>
            <DialogDescription>
              Send a custom email to selected employees. You can send it immediately or schedule it for later.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Template Selection */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Use Email Template (Optional)
              </Label>
              <div className="flex gap-2">
                <Select value={selectedTemplate} onValueChange={handleTemplateSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a template..." />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((template) => (
                      <SelectItem key={template._id} value={template.templateId}>
                        {template.name} ({template.category})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedTemplate && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleClearTemplate}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              {selectedTemplate && (
                <p className="text-xs text-blue-600 dark:text-blue-400">
                  Template applied! You can customize the content below.
                </p>
              )}
            </div>

            {/* Email Subject */}
            <div className="space-y-2">
              <Label htmlFor="subject">Subject *</Label>
              <Input
                id="subject"
                placeholder="Email subject..."
                value={emailForm.subject}
                onChange={(e) => setEmailForm({ ...emailForm, subject: e.target.value })}
              />
            </div>

            {/* Email Message */}
            <div className="space-y-2">
              <Label htmlFor="message">Message *</Label>
              <Textarea
                id="message"
                placeholder="Type your message here..."
                className="min-h-[120px]"
                value={emailForm.message}
                onChange={(e) => setEmailForm({ ...emailForm, message: e.target.value })}
              />
            </div>

            {/* Schedule Options */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Schedule Email (Optional)
              </Label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label htmlFor="scheduleDate" className="text-xs text-muted-foreground">Date</Label>
                  <Input
                    id="scheduleDate"
                    type="date"
                    value={emailForm.scheduleDate}
                    onChange={(e) => setEmailForm({ ...emailForm, scheduleDate: e.target.value })}
                    min={format(new Date(), 'yyyy-MM-dd')}
                  />
                </div>
                <div>
                  <Label htmlFor="scheduleTime" className="text-xs text-muted-foreground">Time</Label>
                  <Input
                    id="scheduleTime"
                    type="time"
                    value={emailForm.scheduleTime}
                    onChange={(e) => setEmailForm({ ...emailForm, scheduleTime: e.target.value })}
                  />
                </div>
              </div>
              {emailForm.scheduleDate && emailForm.scheduleTime && (
                <p className="text-xs text-muted-foreground">
                  Will be sent on: {format(new Date(`${emailForm.scheduleDate}T${emailForm.scheduleTime}`), 'PPpp')}
                </p>
              )}
            </div>

            {/* Employee Selection */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Select Recipients *
                </Label>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="selectAll"
                    checked={selectAll}
                    onCheckedChange={handleSelectAllEmployees}
                  />
                  <label
                    htmlFor="selectAll"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Select All ({employees.length})
                  </label>
                </div>
              </div>

              <div className="border rounded-lg p-3 max-h-[200px] overflow-y-auto space-y-2">
                {employees.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No employees found
                  </p>
                ) : (
                  employees.map((employee) => (
                    <div key={employee._id} className="flex items-center space-x-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded">
                      <Checkbox
                        id={employee._id}
                        checked={selectedEmployees.includes(employee.email)}
                        onCheckedChange={() => handleEmployeeToggle(employee.email)}
                      />
                      <label
                        htmlFor={employee._id}
                        className="flex-1 text-sm cursor-pointer"
                      >
                        <div className="font-medium">{employee.name}</div>
                        <div className="text-xs text-muted-foreground">{employee.email}</div>
                      </label>
                      <Badge variant="outline">{employee.role}</Badge>
                    </div>
                  ))
                )}
              </div>

              {selectedEmployees.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {selectedEmployees.length} employee(s) selected
                </p>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsEmailDialogOpen(false);
                setEmailForm({
                  subject: "",
                  message: "",
                  scheduleDate: "",
                  scheduleTime: "",
                });
                setSelectedEmployees([]);
                setSelectAll(false);
                setSelectedTemplate("");
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSendCustomEmail}
              disabled={loading || selectedEmployees.length === 0}
            >
              {loading ? (
                "Sending..."
              ) : emailForm.scheduleDate && emailForm.scheduleTime ? (
                <>
                  <Clock className="h-4 w-4 mr-2" />
                  Schedule Email
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send Now
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}