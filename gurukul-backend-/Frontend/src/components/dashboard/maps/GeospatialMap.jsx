import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet icon paths in bundler builds
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const STATE_COORDINATES = {
  maharashtra: { center: [19.7515, 75.7139], zoom: 7 },
  madhya_pradesh: { center: [22.9734, 78.6569], zoom: 7 }
};

const DISTRICT_DATA = {
  maharashtra: [
    { name: 'Mumbai', coords: [19.0760, 72.8777], score: 92, schools: 450, activeSessions: 8900 },
    { name: 'Pune', coords: [18.5204, 73.8567], score: 88, schools: 380, activeSessions: 6200 },
    { name: 'Nagpur', coords: [21.1458, 79.0882], score: 85, schools: 310, activeSessions: 4500 },
    { name: 'Nashik', coords: [19.9975, 73.7898], score: 84, schools: 280, activeSessions: 3800 },
    { name: 'Aurangabad', coords: [19.8762, 75.3433], score: 81, schools: 210, activeSessions: 2900 }
  ],
  madhya_pradesh: [
    { name: 'Bhopal', coords: [23.2599, 77.4126], score: 90, schools: 320, activeSessions: 5100 },
    { name: 'Indore', coords: [22.7196, 75.8577], score: 91, schools: 410, activeSessions: 7800 },
    { name: 'Gwalior', coords: [26.2183, 78.1828], score: 83, schools: 240, activeSessions: 3200 },
    { name: 'Jabalpur', coords: [23.1815, 79.9864], score: 82, schools: 220, activeSessions: 3000 },
    { name: 'Ujjain', coords: [23.1764, 75.7885], score: 86, schools: 190, activeSessions: 2400 }
  ]
};

const SCHOOLS_BY_DISTRICT = {
  'Mumbai': [
    { name: 'Mumbai Excellence Academy', activeSessions: 34, rating: '94%', compliance: '1.0' },
    { name: 'South High Central School', activeSessions: 28, rating: '89%', compliance: '0.98' },
    { name: 'Colaba Public Model School', activeSessions: 22, rating: '91%', compliance: '1.0' }
  ],
  'Pune': [
    { name: 'Pune Smart Learner School', activeSessions: 42, rating: '90%', compliance: '1.0' },
    { name: 'Shivaji Memorial Institute', activeSessions: 31, rating: '87%', compliance: '0.95' }
  ],
  'Bhopal': [
    { name: 'Bhopal Central Model School', activeSessions: 25, rating: '92%', compliance: '1.0' },
    { name: 'Lake City Girls Academy', activeSessions: 19, rating: '88%', compliance: '1.0' }
  ],
  'Indore': [
    { name: 'Indore Science High School', activeSessions: 48, rating: '93%', compliance: '1.0' },
    { name: 'Holkar Memorial Academy', activeSessions: 36, rating: '90%', compliance: '0.97' }
  ]
};

const GeospatialMap = ({ selectedState = 'maharashtra', onStateChange }) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersGroupRef = useRef(null);

  const [drilldownDistrict, setDrilldownDistrict] = useState(null);
  const [selectedSchool, setSelectedSchool] = useState(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = L.map(mapContainerRef.current, {
      zoomControl: false,
      attributionControl: false
    });
    mapInstanceRef.current = map;

    // Add dark premium tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    // Zoom controls customized
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Layer group for markers
    const markersGroup = L.layerGroup().addTo(map);
    markersGroupRef.current = markersGroup;

    return () => {
      map.remove();
    };
  }, []);

  // Sync View & Markers when state changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersGroup = markersGroupRef.current;
    if (!map || !markersGroup) return;

    // Clear previous settings
    markersGroup.clearLayers();
    setDrilldownDistrict(null);
    setSelectedSchool(null);

    const config = STATE_COORDINATES[selectedState] || STATE_COORDINATES.maharashtra;
    map.setView(config.center, config.zoom);

    // Create markers
    const districts = DISTRICT_DATA[selectedState] || [];
    districts.forEach(dist => {
      const marker = L.marker(dist.coords);

      const popupContent = `
        <div style="font-family: Inter, sans-serif; color: #1f2937; padding: 4px;">
          <h4 style="margin: 0 0 4px 0; font-weight: 700; font-size: 14px;">${dist.name} District</h4>
          <div style="font-size: 11px; margin-bottom: 2px;">Comprehension Score: <b>${dist.score}%</b></div>
          <div style="font-size: 11px; margin-bottom: 2px;">Active Institutions: <b>${dist.schools}</b></div>
          <div style="font-size: 11px;">Hourly Active Sessions: <b>${dist.activeSessions}</b></div>
        </div>
      `;

      marker.bindPopup(popupContent);
      
      marker.on('click', () => {
        setDrilldownDistrict(dist.name);
        setSelectedSchool(null);
      });

      markersGroup.addLayer(marker);
    });

  }, [selectedState]);

  return (
    <div className="flex flex-col xl:flex-row gap-6 w-full h-[500px]">
      {/* Map Side */}
      <div className="flex-1 rounded-2xl overflow-hidden border border-white/10 relative h-[320px] xl:h-full">
        {/* State Selection Dropdown */}
        <div className="absolute top-4 left-4 z-[1000] bg-black/80 backdrop-blur-md border border-white/10 rounded-xl p-2 flex items-center gap-2">
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">State context:</span>
          <select 
            value={selectedState} 
            onChange={(e) => onStateChange && onStateChange(e.target.value)}
            className="bg-transparent text-xs text-white border-none focus:outline-none cursor-pointer font-bold"
          >
            <option value="maharashtra" className="bg-black text-white">Maharashtra</option>
            <option value="madhya_pradesh" className="bg-black text-white">Madhya Pradesh</option>
          </select>
        </div>

        <div ref={mapContainerRef} className="w-full h-full" />
      </div>

      {/* Drilldown Panel Side */}
      <div className="w-full xl:w-[320px] flex flex-col justify-between border border-white/10 rounded-2xl bg-white/[0.02] p-5">
        <div>
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3 border-b border-white/5 pb-2">
            Geospatial Drilldown
          </h4>

          {!drilldownDistrict ? (
            <div className="text-center py-12 text-gray-500 text-xs">
              Click a district marker on the map to inspect school aggregations.
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Selected District:</div>
                <div className="text-lg font-bold text-white flex items-center gap-1.5 mt-0.5">
                  <span className="h-2 w-2 rounded-full bg-orange-500 inline-block"></span>
                  {drilldownDistrict}
                </div>
              </div>

              {/* Schools list */}
              <div className="space-y-2">
                <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Schools Grid:</div>
                <div className="space-y-1.5 max-h-[200px] overflow-y-auto pr-1 custom-scrollbar">
                  {(SCHOOLS_BY_DISTRICT[drilldownDistrict] || [
                    { name: `${drilldownDistrict} Model Academy`, activeSessions: 12, rating: '84%', compliance: '1.0' },
                    { name: `${drilldownDistrict} Public School`, activeSessions: 8, rating: '81%', compliance: '0.96' }
                  ]).map((school, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedSchool(school)}
                      className={`w-full text-left p-2.5 rounded-xl border text-xs transition-all ${
                        selectedSchool?.name === school.name
                          ? 'bg-orange-600/10 border-orange-500/40 text-white'
                          : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10 hover:text-white'
                      }`}
                    >
                      <div className="font-bold truncate">{school.name}</div>
                      <div className="flex justify-between mt-1 text-[10px] text-gray-500">
                        <span>Sessions: {school.activeSessions}</span>
                        <span>Comprehension: {school.rating}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* School Telemetry Drawer */}
        {selectedSchool && (
          <div className="mt-4 pt-4 border-t border-white/5 space-y-3">
            <div className="text-[10px] font-bold text-orange-400 uppercase tracking-widest">School Telemetry Profile</div>
            <div className="grid grid-cols-2 gap-3 text-xs bg-black/35 p-3 rounded-xl border border-white/5">
              <div>
                <span className="text-gray-500 block text-[9px] uppercase">Compliance</span>
                <span className="font-bold text-emerald-400 font-mono">{selectedSchool.compliance}</span>
              </div>
              <div>
                <span className="text-gray-500 block text-[9px] uppercase">Active Sessions</span>
                <span className="font-bold text-blue-400 font-mono">{selectedSchool.activeSessions}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GeospatialMap;
