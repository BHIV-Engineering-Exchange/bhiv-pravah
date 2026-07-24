// Prevent unhandled errors from crashing the server
process.on('uncaughtException', (err) => {
  console.error('[UNCAUGHT EXCEPTION]', err.message);
});
process.on('unhandledRejection', (reason) => {
  console.error('[UNHANDLED REJECTION]', reason?.message || reason);
});

const express = require("express");
const { createServer } = require("http");
const cors = require("cors");
const mongoose = require("mongoose");

const swaggerUi = require('swagger-ui-express');
const swaggerSpec = require('./docs/swagger');
const authRoutes = require("./routes/authRoutes");
const ttgRoutes = require("./routes/ttgRoutes");
const ttsRoutes = require("./routes/ttsRoutes");
const coreExecutionRoutes = require("./routes/coreExecution");
const pipelineRoutes       = require("./routes/pipeline");
const simulateRoutes       = require("./routes/simulate");
const atharvaRoute         = require("./routes/atharvaRoute");
const svacsRoute           = require("./routes/svacsRoute");
const namamiGangeRoute     = require("./routes/namamiGangeRoute");
const phase5Route          = require("./routes/phase5Route");
const { attachStreamNamespace } = require("./routes/simulate");
const { router: executeRoute } = require("./routes/executionInterface");
const { initSocket } = require("./socket");
const { dispatcherEvents } = require("./executionDispatcher");
const executionRetry = require("./executionRetry");
require("dotenv").config();
const { setupEngineSocket } = require("./engine/engine_socket");
const jobQueue = require("./jobQueue");
const { emitPravahSignal, startHeartbeat } = require("./observability/pravah_adapter");

// Set NODE_ENV if not set
if (!process.env.NODE_ENV) {
  process.env.NODE_ENV = 'development';
  console.log('[CONFIG] NODE_ENV set to development');
}

// Clear job queue on startup
jobQueue.clearAllJobs();
console.log("[STARTUP] Job queue cleared");


const app = express();
const server = createServer(app);

// middleware
app.use(
  cors({
    origin: process.env.FRONTEND_ORIGIN || '*',
    credentials: true,
  })
);
app.use(express.json());

// Global Pravah request latency tracking middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    const duration = Date.now() - start;
    const state = res.statusCode >= 500 ? "error" : "running";
    const errorsLastMin = res.statusCode >= 500 ? 1 : 0;
    emitPravahSignal(state, duration, errorsLastMin);
  });
  next();
});

// API docs
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime(), timestamp: Date.now() });
});

// routes
app.use("/auth", authRoutes);
app.use("/api/intent", ttgRoutes);
app.use("/api/tts", ttsRoutes);
app.use("/core", coreExecutionRoutes);
app.use("/core", atharvaRoute);
app.use("/svacs", svacsRoute);
app.use("/namami-gange", namamiGangeRoute);
app.use("/", phase5Route);
app.use("/pipeline", pipelineRoutes);
app.use("/simulate", simulateRoutes);
app.use("/", executeRoute);  // POST /execute — Phase 4 hardened interface

// db (optional - system works without MongoDB)
if (process.env.MONGO_URI && process.env.MONGO_URI !== 'mongodb://localhost:27017/microbridge') {
  mongoose.connect(process.env.MONGO_URI)
    .then(() => console.log("Mongo connected"))
    .catch(err => {
      console.warn("MongoDB connection failed (non-critical):", err.message);
      console.log("System will continue without database persistence");
    });
} else {
  console.log("MongoDB disabled - using in-memory state only");
}

// sockets
const io = initSocket(server);
app.set('io', io);
global._app = app;  // allows dispatcher to emit job_status without circular dep
setupEngineSocket(io, jobQueue);
attachStreamNamespace(io);  // Phase 1: /simulate/stream delta stream namespace

// Execution monitoring events
dispatcherEvents.on('execution_dispatched', (data) => {
  io.emit('execution:started', {
    execution_id: data.execution_id,
    trace_id: data.trace_id,
    timestamp: Date.now()
  });
});

dispatcherEvents.on('execution_completed', (data) => {
  const { getExecution } = require('./executionRegistry');
  const execution = getExecution(data.execution_id);
  const duration = execution ? execution.completedAt - execution.startedAt : null;
  
  io.emit('execution:completed', {
    execution_id: data.execution_id,
    trace_id: data.trace_id,
    duration,
    timestamp: Date.now()
  });
});

dispatcherEvents.on('execution_failed', (data) => {
  const { getExecution } = require('./executionRegistry');
  const execution = getExecution(data.execution_id);
  
  io.emit('execution:failed', {
    execution_id: data.execution_id,
    trace_id: data.trace_id,
    error: execution?.error || 'Unknown error',
    timestamp: Date.now()
  });
});

executionRetry.on('execution:retry', (data) => {
  io.emit('execution:retry', data);
});

const PORT = process.env.PORT || 3000;

if (!process.env.PORT) {
  console.warn("[CONFIG] PORT not set in environment, using default: 5000");
}

// server
server.listen(PORT, () => {
  console.log(`server running at PORT : ${PORT}`);
  startHeartbeat(60);
});
