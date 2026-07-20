const https = require('https');

/**
 * Reverse geocode coordinates to get detailed address
 * Uses OpenStreetMap Nominatim API (free, no API key required)
 * 
 * @param {number} latitude - Latitude coordinate
 * @param {number} longitude - Longitude coordinate
 * @returns {Promise<Object>} Address details including full address, components, etc.
 */
async function reverseGeocode(latitude, longitude) {
  return new Promise((resolve, reject) => {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`;
    
    const options = {
      headers: {
        'User-Agent': 'Infiverse-Attendance-System/1.0 (https://infiverse.com)',
        'Accept': 'application/json'
      },
      timeout: 10000 // 10 second timeout
    };

    const req = https.get(url, options, (res) => {
      // Check for rate limiting or errors
      if (res.statusCode === 429) {
        console.warn('Nominatim rate limit hit, using fallback');
        fallbackReverseGeocode(latitude, longitude)
          .then(resolve)
          .catch(() => {
            // Last resort: return coordinates
            resolve(createFallbackAddress(latitude, longitude));
          });
        return;
      }

      if (res.statusCode !== 200) {
        console.warn(`Nominatim returned status ${res.statusCode}, using fallback`);
        fallbackReverseGeocode(latitude, longitude)
          .then(resolve)
          .catch(() => {
            resolve(createFallbackAddress(latitude, longitude));
          });
        return;
      }

      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          
          // Check if result has error
          if (result.error) {
            console.warn('Nominatim error:', result.error);
            fallbackReverseGeocode(latitude, longitude)
              .then(resolve)
              .catch(() => {
                resolve(createFallbackAddress(latitude, longitude));
              });
            return;
          }

          const address = result.address || {};
          
          // Build formatted address
          const addressParts = [
            address.house_number,
            address.road,
            address.suburb || address.neighbourhood,
            address.city || address.town || address.village,
            address.state,
            address.postcode,
            address.country
          ].filter(Boolean);
          
          const formattedAddress = addressParts.length > 0 
            ? addressParts.join(', ')
            : result.display_name || `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

          resolve({
            fullAddress: formattedAddress,
            displayName: result.display_name || formattedAddress,
            pincode: address.postcode || address.pincode || null,
            area: address.suburb || address.neighbourhood || address.locality || address.city_district || null,
            city: address.city || address.town || address.village || address.county || null,
            state: address.state || null,
            country: address.country || null,
            road: address.road || address.street || null,
            houseNumber: address.house_number || null,
            raw: result
          });
        } catch (error) {
          console.warn('Error parsing Nominatim response:', error.message);
          // Fallback to bigdatacloud API
          fallbackReverseGeocode(latitude, longitude)
            .then(resolve)
            .catch(() => {
              resolve(createFallbackAddress(latitude, longitude));
            });
        }
      });
    });

    req.on('error', (error) => {
      console.warn('Nominatim request error:', error.message);
      // Fallback to bigdatacloud API
      fallbackReverseGeocode(latitude, longitude)
        .then(resolve)
        .catch(() => {
          resolve(createFallbackAddress(latitude, longitude));
        });
    });

    req.on('timeout', () => {
      req.destroy();
      console.warn('Nominatim request timeout, using fallback');
      fallbackReverseGeocode(latitude, longitude)
        .then(resolve)
        .catch(() => {
          resolve(createFallbackAddress(latitude, longitude));
        });
    });

    req.setTimeout(10000);
  });
}

// Helper function to create fallback address
function createFallbackAddress(latitude, longitude) {
  return {
    fullAddress: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
    displayName: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
    pincode: null,
    area: null,
    city: null,
    state: null,
    country: null,
    road: null,
    houseNumber: null,
    raw: null
  };
}

/**
 * Fallback reverse geocoding using BigDataCloud API
 * 
 * @param {number} latitude - Latitude coordinate
 * @param {number} longitude - Longitude coordinate
 * @returns {Promise<Object>} Address details
 */
async function fallbackReverseGeocode(latitude, longitude) {
  return new Promise((resolve, reject) => {
    const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`;
    
    const req = https.get(url, {
      timeout: 10000
    }, (res) => {
      if (res.statusCode !== 200) {
        resolve(createFallbackAddress(latitude, longitude));
        return;
      }

      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          
          const formattedAddress = result.display_name || 
            `${result.locality || ''}, ${result.countryName || ''}`.trim() ||
            `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;

          resolve({
            fullAddress: formattedAddress,
            displayName: result.display_name || formattedAddress,
            pincode: result.postcode || null,
            area: result.locality || result.city || null,
            city: result.city || result.locality || null,
            state: result.principalSubdivision || null,
            country: result.countryName || null,
            road: null,
            houseNumber: null,
            raw: result
          });
        } catch (error) {
          console.warn('Error parsing BigDataCloud response:', error.message);
          resolve(createFallbackAddress(latitude, longitude));
        }
      });
    });

    req.on('error', (error) => {
      console.warn('BigDataCloud request error:', error.message);
      resolve(createFallbackAddress(latitude, longitude));
    });

    req.on('timeout', () => {
      req.destroy();
      resolve(createFallbackAddress(latitude, longitude));
    });

    req.setTimeout(10000);
  });
}

module.exports = {
  reverseGeocode,
  fallbackReverseGeocode
};

