const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { MongoClient } = require('mongodb');
require('dotenv').config({ path: '../.env' }); // Load .env from parent directory

const app = express();
app.use(express.static(__dirname));
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: ["http://localhost:8000", "http://localhost:8080"],
        methods: ["GET", "POST"]
    }
});

const mongoUri = process.env.MONGODB_URI;
let client;

async function connectMongo() {
    if (!mongoUri) {
        console.error('MONGODB_URI is not defined in the .env file');
        process.exit(1);
    }
    console.log('MongoDB URI:', mongoUri); // Debug line
    if (!mongoUri.startsWith('mongodb://') && !mongoUri.startsWith('mongodb+srv://')) {
        console.error('MONGODB_URI is invalid: must start with mongodb:// or mongodb+srv://');
        process.exit(1);
    }
    try {
        client = new MongoClient(mongoUri, { serverSelectionTimeoutMS: 5000 });
        await client.connect();
        console.log('Connected to MongoDB');
    } catch (error) {
        console.error('MongoDB connection failed:', error);
        process.exit(1);
    }
}

async function storeLog(type, data) {
    try {
        const db = client.db("workflow_ai");
        const logs = db.collection("logs");
        await logs.insertOne({
            agent: type,
            message: JSON.stringify(data),
            timestamp: new Date()
        });
        console.log(`Log stored: ${type}`);
    } catch (error) {
        console.error('Error storing log:', error);
    }
}

io.on('connection', (socket) => {
    console.log('Client connected');
    socket.on('agent-recommendation', async (data) => {
        console.log('Received agent-recommendation:', data);
        await storeLog('agent-recommendation', data);
        io.emit('agent-recommendation', data);
    });
    socket.on('escalation', async (data) => {
        console.log('Received escalation:', data);
        await storeLog('escalation', data);
        io.emit('escalation', data);
    });
    socket.on('dependency-update', async (data) => {
        console.log('Received dependency-update:', data);
        await storeLog('dependency-update', data);
        io.emit('dependency-update', data);
    });
    socket.on('disconnect', () => {
        console.log('Client disconnected');
    });
});

const PORT = process.env.PORT || 5000;
connectMongo().then(() => {
    server.listen(PORT, () => {
        console.log(`Socket.IO server running on port ${PORT}`);
    });
});