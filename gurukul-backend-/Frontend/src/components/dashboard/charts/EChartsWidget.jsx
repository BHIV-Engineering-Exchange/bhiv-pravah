import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const EChartsWidget = ({ option, height = '300px', className = '' }) => {
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // Initialize echarts instance
    const chart = echarts.init(chartRef.current, 'dark', {
      renderer: 'svg' // SVG renderer yields sharper borders/shapes on high DPI screens
    });
    chartInstanceRef.current = chart;

    // Configure options
    chart.setOption({
      backgroundColor: 'transparent',
      textStyle: {
        fontFamily: 'Inter, system-ui, sans-serif'
      },
      ...option
    });

    // Handle resize events
    const handleResize = () => {
      chart.resize();
    };
    window.addEventListener('resize', handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [option]);

  // Keep charts responsive if parent size changes dynamically
  useEffect(() => {
    if (chartInstanceRef.current) {
      chartInstanceRef.current.resize();
    }
  }, [height]);

  return (
    <div 
      ref={chartRef} 
      style={{ width: '100%', height }} 
      className={`relative ${className}`}
    />
  );
};

export default EChartsWidget;
