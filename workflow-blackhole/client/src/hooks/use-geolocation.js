import { useState, useEffect, useCallback } from 'react';
import { toast } from './use-toast';

// Office coordinates (should match server configuration)
// Blackhole Infiverse LLP, Road Number 3, near Hathi Circle, above Bright Connection, Kala Galli, Motilal Nagar II, Goregaon West, Mumbai, Maharashtra
const OFFICE_COORDINATES = {
  latitude: 19.1628987,
  longitude: 72.8355871
};
const OFFICE_RADIUS = 100; // meters
const OFFICE_ADDRESS = "Blackhole Infiverse LLP, Road Number 3, near Hathi Circle, above Bright Connection, Kala Galli, Motilal Nagar II, Goregaon West, Mumbai, Maharashtra 400104";

export const useGeolocation = (options = {}) => {
  const [location, setLocation] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [permission, setPermission] = useState('prompt');

  const defaultOptions = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 300000, // 5 minutes
    ...options
  };

  // Check geolocation support
  const isSupported = 'geolocation' in navigator;

  // Get current position
  const getCurrentPosition = useCallback(async () => {
    if (!isSupported) {
      const error = new Error('Geolocation is not supported by this browser');
      setError(error);
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          defaultOptions
        );
      });

      const locationData = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        altitudeAccuracy: position.coords.altitudeAccuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
        timestamp: position.timestamp
      };

      setLocation(locationData);
      setPermission('granted');
      return locationData;

    } catch (err) {
      let errorMessage = 'Failed to get location';
      
      switch (err.code) {
        case err.PERMISSION_DENIED:
          errorMessage = 'Location access denied by user';
          setPermission('denied');
          break;
        case err.POSITION_UNAVAILABLE:
          errorMessage = 'Location information is unavailable';
          break;
        case err.TIMEOUT:
          errorMessage = 'Location request timed out';
          break;
        default:
          errorMessage = err.message || 'Unknown location error';
          break;
      }

      const error = new Error(errorMessage);
      error.code = err.code;
      setError(error);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isSupported, defaultOptions]);

  // Watch position changes
  const watchPosition = useCallback(() => {
    if (!isSupported) {
      setError(new Error('Geolocation is not supported'));
      return null;
    }

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const locationData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude,
          altitudeAccuracy: position.coords.altitudeAccuracy,
          heading: position.coords.heading,
          speed: position.coords.speed,
          timestamp: position.timestamp
        };
        setLocation(locationData);
        setPermission('granted');
      },
      (err) => {
        setError(new Error(err.message));
        if (err.code === err.PERMISSION_DENIED) {
          setPermission('denied');
        }
      },
      defaultOptions
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, [isSupported, defaultOptions]);

  // Get address from coordinates (reverse geocoding)
  const getAddressFromCoordinates = useCallback(async (lat, lng) => {
    try {
      // Using a free geocoding service (you might want to use Google Maps API in production)
      const response = await fetch(
        `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=en`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch address');
      }

      const data = await response.json();
      return {
        address: data.display_name || `${data.locality}, ${data.countryName}`,
        city: data.city || data.locality,
        country: data.countryName,
        countryCode: data.countryCode,
        postcode: data.postcode,
        region: data.principalSubdivision
      };
    } catch (error) {
      console.warn('Failed to get address:', error);
      return {
        address: `${lat.toFixed(6)}, ${lng.toFixed(6)}`,
        city: 'Unknown',
        country: 'Unknown'
      };
    }
  }, []);

  // Calculate distance between two points
  const calculateDistance = useCallback((lat1, lng1, lat2, lng2) => {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI/180;
    const φ2 = lat2 * Math.PI/180;
    const Δφ = (lat2-lat1) * Math.PI/180;
    const Δλ = (lng2-lng1) * Math.PI/180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c; // Distance in meters
  }, []);

  // Check if user is within a specific radius of a location
  const isWithinRadius = useCallback((targetLat, targetLng, radius, userLat = location?.latitude, userLng = location?.longitude) => {
    if (!userLat || !userLng) return false;
    
    const distance = calculateDistance(userLat, userLng, targetLat, targetLng);
    return {
      isWithin: distance <= radius,
      distance,
      accuracy: location?.accuracy || 0
    };
  }, [location, calculateDistance]);

  // Request permission explicitly
  const requestPermission = useCallback(async () => {
    if (!isSupported) {
      setError(new Error('Geolocation is not supported'));
      return 'unsupported';
    }

    try {
      const result = await navigator.permissions.query({ name: 'geolocation' });
      setPermission(result.state);
      
      if (result.state === 'granted') {
        await getCurrentPosition();
      }
      
      return result.state;
    } catch (error) {
      // Fallback for browsers that don't support permissions API
      try {
        await getCurrentPosition();
        return 'granted';
      } catch (err) {
        return 'denied';
      }
    }
  }, [isSupported, getCurrentPosition]);

  // Auto-request location on mount if needed
  useEffect(() => {
    if (options.autoRequest && isSupported && permission === 'prompt') {
      requestPermission();
    }
  }, [options.autoRequest, isSupported, permission, requestPermission]);

  // Utility function to format coordinates
  const formatCoordinates = useCallback((lat, lng, precision = 6) => {
    if (typeof lat !== 'number' || typeof lng !== 'number') return 'Invalid coordinates';
    return `${lat.toFixed(precision)}, ${lng.toFixed(precision)}`;
  }, []);

  // Get location with address
  const getCurrentLocationWithAddress = useCallback(async () => {
    const position = await getCurrentPosition();
    if (!position) return null;

    const address = await getAddressFromCoordinates(position.latitude, position.longitude);
    return {
      ...position,
      ...address
    };
  }, [getCurrentPosition, getAddressFromCoordinates]);

  return {
    // State
    location,
    error,
    loading,
    permission,
    isSupported,

    // Actions
    getCurrentPosition,
    getCurrentLocationWithAddress,
    watchPosition,
    requestPermission,
    getAddressFromCoordinates,

    // Utilities
    calculateDistance,
    isWithinRadius,
    formatCoordinates,

    // Computed values
    hasLocation: !!location,
    isPermissionGranted: permission === 'granted',
    isPermissionDenied: permission === 'denied',
    accuracy: location?.accuracy || 0,
    coordinates: location ? {
      lat: location.latitude,
      lng: location.longitude
    } : null
  };
};

// Hook for office location validation
export const useOfficeLocationValidation = (officeCoordinates, radius = 100) => {
  const geolocation = useGeolocation({ autoRequest: false });
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);

  const validateLocation = useCallback(async () => {
    if (!officeCoordinates) {
      toast({
        title: "Configuration Error",
        description: "Office location not configured",
        variant: "destructive"
      });
      return false;
    }

    setIsValidating(true);
    
    try {
      const position = await geolocation.getCurrentPosition();
      if (!position) {
        throw new Error('Could not get current location');
      }

      const result = geolocation.isWithinRadius(
        officeCoordinates.latitude,
        officeCoordinates.longitude,
        radius,
        position.latitude,
        position.longitude
      );

      setValidationResult({
        ...result,
        position,
        officeCoordinates,
        radius,
        timestamp: new Date()
      });

      if (!result.isWithin) {
        toast({
          title: "Location Validation Failed",
          description: `You must be within ${radius}m of the office. Current distance: ${Math.round(result.distance)}m. Please visit: ${OFFICE_ADDRESS}`,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Location Validated",
          description: `You are within the office premises (${Math.round(result.distance)}m away)`,
          variant: "default"
        });
      }

      return result.isWithin;

    } catch (error) {
      console.error('Location validation error:', error);
      toast({
        title: "Location Error",
        description: error.message,
        variant: "destructive"
      });
      return false;
    } finally {
      setIsValidating(false);
    }
  }, [geolocation, officeCoordinates, radius]);

  return {
    ...geolocation,
    validationResult,
    isValidating,
    validateLocation,
    isLocationValid: validationResult?.isWithin || false,
    distanceFromOffice: validationResult?.distance || null
  };
};
