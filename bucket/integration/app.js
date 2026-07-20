const socket = io('http://localhost:5000');

socket.on('connect', () => {
    console.log('Connected to Socket.IO server');
});

socket.on('agent-recommendation', (data) => {
    addLogEntry('Agent Recommendation', data);
});

socket.on('escalation', (data) => {
    addLogEntry('Escalation', data);
});

socket.on('dependency-update', (data) => {
    addLogEntry('Dependency Update', data);
});

function addLogEntry(type, data) {
    const logContainer = document.getElementById('log-container');
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `<strong>${type}</strong> (${new Date().toLocaleString()}): ${JSON.stringify(data)}`;
    logContainer.appendChild(logEntry);
}

document.addEventListener('DOMContentLoaded', () => {
    const logContainer = document.getElementById('log-container');
    const initialMsg = document.createElement('div');
    initialMsg.className = 'log-entry';
    initialMsg.textContent = 'Connected to log server. Waiting for new logs...';
    logContainer.appendChild(initialMsg);
});