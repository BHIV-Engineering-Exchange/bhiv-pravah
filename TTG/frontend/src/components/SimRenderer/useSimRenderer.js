import { useRef, useEffect, useCallback } from 'react';
import CanvasRenderer from './CanvasRenderer';

/**
 * useSimRenderer
 *
 * Manages CanvasRenderer lifecycle inside a React component.
 *
 * Usage:
 *   const { canvasRef, renderResult, renderHeadless } = useSimRenderer(simResult);
 *
 * @param {Object|null} simResult   - Output of SimEngine.run()
 * @param {Object}      [opts]
 * @param {number}      [opts.width=600]
 * @param {number}      [opts.height=600]
 * @param {number}      [opts.interval_ms=150]  - Animation frame interval
 * @param {boolean}     [opts.headless=false]
 */
export default function useSimRenderer(simResult, opts = {}) {
  const canvasRef    = useRef(null);
  const rendererRef  = useRef(null);
  const animationRef = useRef(null);

  const width       = opts.width       || 600;
  const height      = opts.height      || 600;
  const interval_ms = opts.interval_ms || 150;

  // Mount renderer once
  useEffect(() => {
    if (opts.headless) {
      rendererRef.current = new CanvasRenderer({ width, height, headless: true });
      return;
    }
    if (!canvasRef.current) return;

    rendererRef.current = new CanvasRenderer({
      canvas: canvasRef.current,
      width,
      height
    });

    return () => {
      if (animationRef.current) animationRef.current.stop();
      rendererRef.current = null;
    };
  }, []);   // eslint-disable-line react-hooks/exhaustive-deps

  // Re-render whenever simResult changes
  useEffect(() => {
    if (!simResult || !rendererRef.current) return;
    if (animationRef.current) animationRef.current.stop();

    const renderer = rendererRef.current;

    // Fit viewport to entity positions
    renderer.fitViewport(simResult.entities);

    if (simResult.tick_snapshots && simResult.tick_snapshots.length > 0) {
      // Animate through tick snapshots
      animationRef.current = renderer.animate(
        simResult.tick_snapshots,
        simResult.entities,
        simResult.zones,
        simResult.flags,
        simResult.blocked,
        interval_ms
      );
    } else {
      // Static render of final state
      renderer.render({
        entities: simResult.entities,
        zones:    simResult.zones    || {},
        flags:    simResult.flags    || {},
        blocked:  simResult.blocked  || {},
        tick:     simResult.ticks_run || 0,
        trace_id: simResult.trace_id
      });
    }

    renderer.drawLegend();

    return () => {
      if (animationRef.current) animationRef.current.stop();
    };
  }, [simResult, interval_ms]);

  // Headless export — returns frame snapshots as JSON
  const renderHeadless = useCallback((result) => {
    const r = result || simResult;
    if (!r) return [];

    const hr = new CanvasRenderer({ width, height, headless: true });
    hr.fitViewport(r.entities);

    return hr.renderHeadless(
      r.tick_snapshots || [],
      r.zones   || {},
      r.flags   || {},
      r.blocked || {}
    );
  }, [simResult, width, height]);

  return { canvasRef, renderHeadless };
}
