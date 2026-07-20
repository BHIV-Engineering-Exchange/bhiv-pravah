import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const HolidaysEvents = () => {
  const [holidays, setHolidays] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showHolidayForm, setShowHolidayForm] = useState(false);
  const [showEventForm, setShowEventForm] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState(null);
  const [editingEvent, setEditingEvent] = useState(null);

  const [holidayForm, setHolidayForm] = useState({
    name: '',
    start_date: '',
    end_date: '',
    description: '',
  });

  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    event_date: '',
    event_time: '',
    event_type: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [holidaysData, eventsData] = await Promise.all([
        schoolAdminAPI.getHolidays(),
        schoolAdminAPI.getEvents(),
      ]);
      setHolidays(holidaysData);
      setEvents(eventsData);
      setError('');
    } catch (err) {
      console.error('Error fetching holidays/events:', err);
      setError('Failed to load holidays and events. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateHoliday = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createHoliday(holidayForm);
      setShowHolidayForm(false);
      setEditingHoliday(null);
      setHolidayForm({ name: '', start_date: '', end_date: '', description: '' });
      fetchData();
      alert('Holiday created successfully!');
    } catch (err) {
      console.error('Error creating holiday:', err);
      alert(err.response?.data?.detail || 'Failed to create holiday');
    }
  };

  const handleEditHoliday = (holiday) => {
    setEditingHoliday(holiday);
    setHolidayForm({
      name: holiday.name,
      start_date: holiday.start_date,
      end_date: holiday.end_date,
      description: holiday.description || '',
    });
    setShowHolidayForm(true);
  };

  const handleUpdateHoliday = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateHoliday(editingHoliday.id, holidayForm);
      setShowHolidayForm(false);
      setEditingHoliday(null);
      setHolidayForm({ name: '', start_date: '', end_date: '', description: '' });
      fetchData();
      alert('Holiday updated successfully!');
    } catch (err) {
      console.error('Error updating holiday:', err);
      alert(err.response?.data?.detail || 'Failed to update holiday');
    }
  };

  const handleDeleteHoliday = async (id) => {
    if (!window.confirm('Are you sure you want to delete this holiday?')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteHoliday(id);
      fetchData();
      alert('Holiday deleted successfully!');
    } catch (err) {
      console.error('Error deleting holiday:', err);
      alert(err.response?.data?.detail || 'Failed to delete holiday');
    }
  };

  const handleCancelHoliday = () => {
    setShowHolidayForm(false);
    setEditingHoliday(null);
    setHolidayForm({ name: '', start_date: '', end_date: '', description: '' });
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createEvent(eventForm);
      setShowEventForm(false);
      setEditingEvent(null);
      setEventForm({ title: '', description: '', event_date: '', event_time: '', event_type: '' });
      fetchData();
      alert('Event created successfully!');
    } catch (err) {
      console.error('Error creating event:', err);
      alert(err.response?.data?.detail || 'Failed to create event');
    }
  };

  const handleEditEvent = (event) => {
    setEditingEvent(event);
    setEventForm({
      title: event.title,
      description: event.description || '',
      event_date: event.event_date,
      event_time: event.event_time || '',
      event_type: event.event_type,
    });
    setShowEventForm(true);
  };

  const handleUpdateEvent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateEvent(editingEvent.id, eventForm);
      setShowEventForm(false);
      setEditingEvent(null);
      setEventForm({ title: '', description: '', event_date: '', event_time: '', event_type: '' });
      fetchData();
      alert('Event updated successfully!');
    } catch (err) {
      console.error('Error updating event:', err);
      alert(err.response?.data?.detail || 'Failed to update event');
    }
  };

  const handleDeleteEvent = async (id) => {
    if (!window.confirm('Are you sure you want to delete this event?')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteEvent(id);
      fetchData();
      alert('Event deleted successfully!');
    } catch (err) {
      console.error('Error deleting event:', err);
      alert(err.response?.data?.detail || 'Failed to delete event');
    }
  };

  const handleCancelEvent = () => {
    setShowEventForm(false);
    setEditingEvent(null);
    setEventForm({ title: '', description: '', event_date: '', event_time: '', event_type: '' });
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading holidays and events...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Holidays & Events</h1>
          <p className="text-gray-400 mt-2">Manage holidays, exams, PTM, and other events</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowHolidayForm(!showHolidayForm)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            ➕ Add Holiday
          </button>
          <button
            onClick={() => setShowEventForm(!showEventForm)}
            className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
          >
            ➕ Add Event
          </button>
        </div>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {showHolidayForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingHoliday ? 'Edit Holiday' : 'Create Holiday'}
          </h2>
          <form onSubmit={editingHoliday ? handleUpdateHoliday : handleCreateHoliday} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Name *</label>
              <input
                type="text"
                required
                value={holidayForm.name}
                onChange={(e) => setHolidayForm({ ...holidayForm, name: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Start Date *</label>
                <input
                  type="date"
                  required
                  value={holidayForm.start_date}
                  onChange={(e) => setHolidayForm({ ...holidayForm, start_date: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">End Date *</label>
                <input
                  type="date"
                  required
                  value={holidayForm.end_date}
                  onChange={(e) => setHolidayForm({ ...holidayForm, end_date: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Description</label>
              <textarea
                value={holidayForm.description}
                onChange={(e) => setHolidayForm({ ...holidayForm, description: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                rows={3}
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                {editingHoliday ? 'Update Holiday' : 'Create Holiday'}
              </button>
              <button
                type="button"
                onClick={handleCancelHoliday}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {showEventForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingEvent ? 'Edit Event' : 'Create Event'}
          </h2>
          <form onSubmit={editingEvent ? handleUpdateEvent : handleCreateEvent} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Title *</label>
              <input
                type="text"
                required
                value={eventForm.title}
                onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Date *</label>
                <input
                  type="date"
                  required
                  value={eventForm.event_date}
                  onChange={(e) => setEventForm({ ...eventForm, event_date: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Time</label>
                <input
                  type="time"
                  value={eventForm.event_time}
                  onChange={(e) => setEventForm({ ...eventForm, event_time: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Type *</label>
              <input
                type="text"
                required
                value={eventForm.event_type}
                onChange={(e) => setEventForm({ ...eventForm, event_type: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                placeholder="e.g., Exam, PTM, Annual Day"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Description</label>
              <textarea
                value={eventForm.description}
                onChange={(e) => setEventForm({ ...eventForm, description: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                rows={3}
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
              >
                {editingEvent ? 'Update Event' : 'Create Event'}
              </button>
              <button
                type="button"
                onClick={handleCancelEvent}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Holidays List */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">Holidays ({holidays.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Start Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  End Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {holidays.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                    No holidays defined
                  </td>
                </tr>
              ) : (
                holidays.map((holiday) => (
                  <tr key={holiday.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {holiday.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {holiday.start_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {holiday.end_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {holiday.description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditHoliday(holiday)}
                          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                          title="Edit"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDeleteHoliday(holiday.id)}
                          className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition"
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Events List */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">Events ({events.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {events.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No events defined
                  </td>
                </tr>
              ) : (
                events.map((event) => (
                  <tr key={event.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {event.title}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {event.event_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {event.event_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {event.event_time || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {event.description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditEvent(event)}
                          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                          title="Edit"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDeleteEvent(event.id)}
                          className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition"
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default HolidaysEvents;

