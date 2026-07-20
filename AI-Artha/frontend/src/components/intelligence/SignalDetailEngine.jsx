/**
 * SignalDetailEngine.jsx
 *
 * Phase 2A — SETU Dispatch Runtime Proof
 * Converts "SEND TO SETU" from placeholder to verified contract.
 *
 * Dispatch states:
 *   idle → dispatching → success (with setu_signal_id) | failed (with exact error) | timeout
 *
 * No fake queue success. If SETU unavailable: UI says exactly that.
 */

import { useState } from 'react';
import toast from 'react-hot-toast';
import { Send, Lightbulb, ShieldAlert, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { Card, Badge, Button } from '../common';
import SignalTracePanel from './SignalTracePanel';
import api from '../../services/api';

const severityBadge = { HIGH: 'danger', MEDIUM: 'warning', LOW: 'success', CRITICAL: 'danger' };

const DISPATCH_STATE = {
  IDLE:        'IDLE',
  DISPATCHING: 'DISPATCHING',
  SUCCESS:     'SUCCESS',
  FAILED:      'FAILED',
  TIMEOUT:     'TIMEOUT',
};

const DispatchResult = ({ state, result }) => {
  if (state === DISPATCH_STATE.IDLE) return null;

  if (state === DISPATCH_STATE.DISPATCHING) {
    return (
      <div className="rounded-xl border border-border/40 bg-muted/30 p-3 text-xs text-muted-foreground flex items-center gap-2">
        <Clock className="w-3.5 h-3.5 animate-pulse" />
        Dispatching to SETU...
      </div>
    );
  }

  if (state === DISPATCH_STATE.SUCCESS) {
    const notDispatched = result?.not_dispatched;
    return (
      <div className="rounded-xl border border-success/30 bg-success/10 p-3 space-y-1.5">
        <div className="flex items-center gap-2 text-success text-xs font-semibold">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {notDispatched ? 'PIPELINE VALIDATED — SETU NOT CONFIGURED' : 'SETU DISPATCH CONFIRMED'}
        </div>
        {notDispatched && (
          <p className="text-xs text-muted-foreground">{result.reason}</p>
        )}
        {result?.dispatched_at && (
          <p className="text-xs text-muted-foreground">
            dispatched at {new Date(result.dispatched_at).toLocaleTimeString()}
            {result.setu_status && ` — HTTP ${result.setu_status}`}
          </p>
        )}
        {result?.warnings?.length > 0 && (
          <p className="text-xs text-warning">Warnings: {result.warnings.join('; ')}</p>
        )}
        {result?.payload && (
          <details className="text-xs">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              {notDispatched ? 'View validated payload' : 'View dispatched payload'}
            </summary>
            <pre className="mt-1 bg-background/60 rounded p-2 overflow-x-auto whitespace-pre-wrap break-all">
              {JSON.stringify(result.payload, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  }

  if (state === DISPATCH_STATE.TIMEOUT) {
    return (
      <div className="rounded-xl border border-warning/30 bg-warning/10 p-3 text-xs space-y-1">
        <div className="flex items-center gap-2 text-warning font-semibold">
          <Clock className="w-3.5 h-3.5" />
          SETU UNAVAILABLE — REQUEST TIMED OUT
        </div>
        <p className="text-muted-foreground">
          {result?.reason || 'Signal was persisted locally. SETU did not respond within timeout.'}
        </p>
        {result?.payload && (
          <details className="text-xs">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">View payload that was attempted</summary>
            <pre className="mt-1 bg-background/60 rounded p-2 overflow-x-auto whitespace-pre-wrap break-all">
              {JSON.stringify(result.payload, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  }

  // FAILED
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-xs space-y-1">
      <div className="flex items-center gap-2 text-destructive font-semibold">
        <XCircle className="w-3.5 h-3.5" />
        SETU DISPATCH FAILED
      </div>
      <p className="text-muted-foreground">
        {result?.error || 'Unknown error. Check backend logs.'}
      </p>
      {result?.status && (
        <p className="text-muted-foreground font-mono">HTTP {result.status}</p>
      )}
      {result?.payload && (
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground">View payload that failed</summary>
          <pre className="mt-1 bg-background/60 rounded p-2 overflow-x-auto whitespace-pre-wrap break-all">
            {JSON.stringify(result.payload, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};

const SignalDetailEngine = ({ selectedSignal }) => {
  const [dispatchState, setDispatchState] = useState(DISPATCH_STATE.IDLE);
  const [dispatchResult, setDispatchResult] = useState(null);
  const [showTrace, setShowTrace] = useState(false);

  const handleSendToSetu = async () => {
    if (!selectedSignal) return;

    setDispatchState(DISPATCH_STATE.DISPATCHING);
    setDispatchResult(null);

    const signalId = selectedSignal.signal_id;

    if (!signalId) {
      setDispatchState(DISPATCH_STATE.FAILED);
      setDispatchResult({
        error: 'This signal has no signal_id — it is a snapshot-derived signal and cannot be dispatched to SETU directly. Persist it first via the compliance filing flow.',
      });
      return;
    }

    try {
      // POST /api/v1/signals/:signalId/dispatch
      // Real HTTP attempt — backend runs normalize→validate→map→serialize→dispatch
      const res = await api.post(`/signals/${signalId}/dispatch`, {}, { timeout: 10000 });
      const result = res.data;

      if (result.dispatch_attempted === false) {
        // Pipeline passed but SETU not configured — show payload proof
        setDispatchState(DISPATCH_STATE.SUCCESS);
        setDispatchResult({
          not_dispatched: true,
          reason: result.reason,
          payload: result.payload,
          headers: result.headers,
          warnings: result.warnings,
        });
        toast.success('Pipeline validated. SETU not configured — payload proof available.');
        return;
      }

      // Actual dispatch succeeded
      setDispatchState(DISPATCH_STATE.SUCCESS);
      setDispatchResult({
        dispatched_at: result.dispatched_at,
        setu_status: result.setu_status,
        setu_response: result.setu_response,
        payload: result.payload,
        headers: result.headers,
        warnings: result.warnings,
      });
      toast.success(`Signal dispatched to SETU — HTTP ${result.setu_status}`);

    } catch (e) {
      if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
        setDispatchState(DISPATCH_STATE.TIMEOUT);
        setDispatchResult(null);
        toast.error('SETU dispatch timed out.');
        return;
      }

      const data = e.response?.data;

      // 422 = pipeline validation failed
      if (e.response?.status === 422) {
        setDispatchState(DISPATCH_STATE.FAILED);
        setDispatchResult({
          error: `Pipeline failed at stage ${data?.pipeline_stage}: ${data?.pipeline_error}`,
          payload: null,
        });
        toast.error(`SETU pipeline failed: ${data?.pipeline_error}`);
        return;
      }

      // 502 = SETU unreachable / timeout / error
      if (e.response?.status === 502) {
        const isTimeout = data?.failure_reason === 'SETU_TIMEOUT';
        if (isTimeout) {
          setDispatchState(DISPATCH_STATE.TIMEOUT);
          setDispatchResult({ reason: data?.failure_message, payload: data?.payload });
          toast.error('SETU did not respond within timeout.');
        } else {
          setDispatchState(DISPATCH_STATE.FAILED);
          setDispatchResult({
            error: `${data?.failure_reason}: ${data?.failure_message}`,
            status: data?.setu_status,
            payload: data?.payload,
          });
          toast.error(`SETU dispatch failed: ${data?.failure_reason}`);
        }
        return;
      }

      setDispatchState(DISPATCH_STATE.FAILED);
      setDispatchResult({
        error: data?.message || e.message,
        status: e.response?.status,
      });
      toast.error(`Dispatch failed: ${data?.message || e.message}`);
    }
  };

  if (!selectedSignal) {
    return (
      <Card className="p-4 sticky top-24">
        <h2 className="text-base font-semibold text-foreground mb-2">Signal Engine</h2>
        <p className="text-sm text-muted-foreground">
          Select a signal from the left panel to inspect reason, recommendation, and trace.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-3 sticky top-24">
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-foreground">Signal Engine</h2>
          <Badge variant={severityBadge[selectedSignal.severity] || 'default'}>
            {selectedSignal.severity}
          </Badge>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Signal Type</p>
            <p className="text-sm font-medium text-foreground font-mono">
              {selectedSignal.type || selectedSignal.signal_type || '—'}
            </p>
          </div>

          <div className="rounded-xl border border-border/60 p-3 bg-muted/30">
            <div className="flex items-center gap-2 mb-1">
              <ShieldAlert className="w-4 h-4 text-warning" />
              <p className="text-xs font-semibold text-muted-foreground tracking-wide">REASON</p>
            </div>
            <p className="text-sm text-foreground">
              {selectedSignal.reason || selectedSignal.context?.reason || 'No reason provided.'}
            </p>
          </div>

          <div className="rounded-xl border border-border/60 p-3 bg-muted/30">
            <div className="flex items-center gap-2 mb-1">
              <Lightbulb className="w-4 h-4 text-primary" />
              <p className="text-xs font-semibold text-muted-foreground tracking-wide">RECOMMENDATION</p>
            </div>
            <p className="text-sm text-foreground">
              {selectedSignal.recommendation || 'Review this signal with finance owner.'}
            </p>
          </div>

          <DispatchResult state={dispatchState} result={dispatchResult} />

          <div className="flex gap-2">
            <Button
              variant="primary"
              className="flex-1"
              icon={Send}
              loading={dispatchState === DISPATCH_STATE.DISPATCHING}
              disabled={dispatchState === DISPATCH_STATE.DISPATCHING}
              onClick={handleSendToSetu}
            >
              SEND TO SETU
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={() => { setShowTrace(t => !t); setDispatchState(DISPATCH_STATE.IDLE); }}
            >
              {showTrace ? 'Hide' : 'Trace'}
            </Button>
          </div>
        </div>
      </Card>

      {showTrace && <SignalTracePanel signal={selectedSignal} />}
    </div>
  );
};

export default SignalDetailEngine;
