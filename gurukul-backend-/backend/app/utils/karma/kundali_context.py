"""
Vedic Astrology (Kundali) Context Layer

Implements Kundali as READ-ONLY CONTEXT
- User DOB
- Time of Birth (optional)  
- Place of Birth (IP-derived fallback)
- Does NOT decide karma
- Does NOT emit signals
- Only provides contextual weighting
"""

import math
from datetime import datetime, date, time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MoonSign(Enum):
    """Vedic Moon Signs (Rashis)"""
    MESHA = "Aries"
    VRISHABA = "Taurus"
    MITHUNA = "Gemini"
    KARKATA = "Cancer"
    SIMHA = "Leo"
    KANYA = "Virgo"
    TULA = "Libra"
    VRISHIKA = "Scorpio"
    DHANUS = "Sagittarius"
    MAKARA = "Capricorn"
    KUMBHA = "Aquarius"
    MEENA = "Pisces"


class Planet(Enum):
    """Vedic Planets"""
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"


@dataclass
class BirthDetails:
    """Birth details for Kundali calculation"""
    dob: date
    tob: Optional[time] = None  # Time of birth (optional)
    place_of_birth: Optional[str] = None  # IP-derived fallback
    partial_kundali: bool = False  # True if TOB missing


@dataclass
class KundaliData:
    """Complete Kundali data structure"""
    moon_sign: MoonSign
    sun_sign: Optional[MoonSign] = None
    ascendant: Optional[MoonSign] = None
    planetary_positions: Dict[Planet, MoonSign] = None
    nakshatra: Optional[str] = None  # Lunar mansion
    kundali_strength: float = 0.5  # 0.0 to 1.0 (based on completeness)
    created_at: datetime = None
    partial: bool = False  # True if partial data


class KundaliCalculator:
    """Calculates Vedic astrology data from birth details"""
    
    def __init__(self):
        # Basic mapping of months to approximate moon signs
        # In a real implementation, this would use precise astronomical calculations
        self.month_to_moon_sign = {
            3: MoonSign.MESHA, 4: MoonSign.VRISHABA, 5: MoonSign.MITHUNA,
            6: MoonSign.KARKATA, 7: MoonSign.SIMHA, 8: MoonSign.KANYA,
            9: MoonSign.TULA, 10: MoonSign.VRISHIKA, 11: MoonSign.DHANUS,
            12: MoonSign.MAKARA, 1: MoonSign.KUMBHA, 2: MoonSign.MEENA
        }
    
    def calculate_kundali(self, birth_details: BirthDetails) -> KundaliData:
        """Calculate Kundali from birth details"""
        # Calculate moon sign based on month (simplified)
        moon_sign = self._calculate_moon_sign(birth_details.dob, birth_details.tob)
        
        # Calculate sun sign (approximate)
        sun_sign = self._calculate_sun_sign(birth_details.dob)
        
        # Calculate other elements based on availability of TOB
        ascendant = None
        nakshatra = None
        planetary_positions = {}
        
        if birth_details.tob is not None:
            # Full calculation possible with TOB
            ascendant = self._calculate_ascendant(birth_details)
            nakshatra = self._calculate_nakshatra(birth_details)
            planetary_positions = self._calculate_planetary_positions(birth_details)
            kundali_strength = 0.9
            partial = False
        else:
            # Day-level calculation only
            kundali_strength = 0.3
            partial = True
            print(f"⚠️  Partial Kundali generated for {birth_details.dob} - Time of birth missing")
        
        return KundaliData(
            moon_sign=moon_sign,
            sun_sign=sun_sign,
            ascendant=ascendant,
            planetary_positions=planetary_positions,
            nakshatra=nakshatra,
            kundali_strength=kundali_strength,
            created_at=datetime.utcnow(),
            partial=partial
        )
    
    def _calculate_moon_sign(self, dob: date, tob: Optional[time]) -> MoonSign:
        """Calculate moon sign from birth details (simplified)"""
        # In reality, moon sign depends on exact lunar position at birth time
        # This is a simplified approximation based on solar month
        month = dob.month
        day = dob.day
        
        # More precise calculation based on month and day
        if month == 3:  # March
            return MoonSign.PISCES if day <= 13 else MoonSign.MESHA
        elif month == 4:  # April
            return MoonSign.MESHA if day <= 12 else MoonSign.VRISHABA
        elif month == 5:  # May
            return MoonSign.VRISHABA if day <= 11 else MoonSign.MITHUNA
        elif month == 6:  # June
            return MoonSign.MITHUNA if day <= 11 else MoonSign.KARKATA
        elif month == 7:  # July
            return MoonSign.KARKATA if day <= 11 else MoonSign.SIMHA
        elif month == 8:  # August
            return MoonSign.SIMHA if day <= 11 else MoonSign.KANYA
        elif month == 9:  # September
            return MoonSign.KANYA if day <= 12 else MoonSign.TULA
        elif month == 10:  # October
            return MoonSign.TULA if day <= 11 else MoonSign.VRISHIKA
        elif month == 11:  # November
            return MoonSign.VRISHIKA if day <= 11 else MoonSign.DHANUS
        elif month == 12:  # December
            return MoonSign.DHANUS if day <= 11 else MoonSign.MAKARA
        elif month == 1:  # January
            return MoonSign.MAKARA if day <= 11 else MoonSign.KUMBHA
        elif month == 2:  # February
            return MoonSign.KUMBHA if day <= 10 else MoonSign.MEENA
        else:  # March (again, for leap years)
            return MoonSign.MEENA if day <= 13 else MoonSign.MESHA
    
    def _calculate_sun_sign(self, dob: date) -> MoonSign:
        """Calculate sun sign from birth date (Western approximation)"""
        month = dob.month
        day = dob.day
        
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return MoonSign.MESHA
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return MoonSign.VRISHABA
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return MoonSign.MITHUNA
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return MoonSign.KARKATA
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return MoonSign.SIMHA
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return MoonSign.KANYA
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return MoonSign.TULA
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return MoonSign.VRISHIKA
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return MoonSign.DHANUS
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            return MoonSign.MAKARA
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return MoonSign.KUMBHA
        else:  # Feb 19 - Mar 20
            return MoonSign.MEENA
    
    def _calculate_ascendant(self, birth_details: BirthDetails) -> MoonSign:
        """Calculate ascendant (Lagna) - requires precise time"""
        # Simplified calculation - in reality this requires precise birth time and location
        # This is a placeholder for a complex astronomical calculation
        return self._calculate_moon_sign(birth_details.dob, birth_details.tob)
    
    def _calculate_nakshatra(self, birth_details: BirthDetails) -> str:
        """Calculate Nakshatra (lunar mansion) - requires precise time"""
        # Simplified calculation
        day_ratio = birth_details.dob.day / 30.0  # Rough approximation
        nakshatra_list = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", 
            "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
            "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", 
            "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
            "Purva Ashadha", "Uttara Ashadha", "Shravana", 
            "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", 
            "Uttara Bhadrapada", "Revati"
        ]
        
        index = int(day_ratio * len(nakshatra_list)) % len(nakshatra_list)
        return nakshatra_list[index]
    
    def _calculate_planetary_positions(self, birth_details: BirthDetails) -> Dict[Planet, MoonSign]:
        """Calculate planetary positions"""
        # Simplified - in reality this requires complex astronomical calculations
        positions = {}
        for planet in Planet:
            # Assign each planet to a sign based on position in list
            sign_index = (planet.value.__hash__() + birth_details.dob.day) % 12
            sign = list(MoonSign)[sign_index]
            positions[planet] = sign
        return positions


class KundaliContextProvider:
    """Provides Kundali context for karma calculations"""
    
    def __init__(self):
        self.calculator = KundaliCalculator()
        self.kundali_store = {}  # Store for user kundalis
    
    def create_user_kundali(self, user_id: str, dob: date, tob: Optional[time] = None, 
                           place_of_birth: Optional[str] = None) -> KundaliData:
        """Create and store user's kundali"""
        birth_details = BirthDetails(
            dob=dob,
            tob=tob,
            place_of_birth=place_of_birth,
            partial_kundali=(tob is None)
        )
        
        kundali = self.calculator.calculate_kundali(birth_details)
        
        # Store in memory (in production, this would go to DB)
        self.kundali_store[user_id] = {
            'kundali': kundali,
            'birth_details': birth_details,
            'created_at': datetime.utcnow()
        }
        
        return kundali
    
    def get_contextual_weighting(self, user_id: str) -> Dict[str, float]:
        """Get contextual weighting based on kundali - does NOT override karma"""
        if user_id not in self.kundali_store:
            return {"kundali_influence": 0.0, "note": "No kundali available"}
        
        kundali = self.kundali_store[user_id]['kundali']
        
        # Calculate influence weights based on kundali strength and planetary positions
        # These weights are for contextual awareness only, NOT for determining karma
        weights = {
            "kundali_influence": kundali.kundali_strength,
            "moon_sign_influence": 0.1,  # Low influence - karma is primary
            "sun_sign_influence": 0.05,  # Very low influence
            "nakshatra_influence": 0.05, # Very low influence
            "ascendant_influence": 0.1 if kundali.ascendant else 0.0,  # Only if available
            "note": "Kundali provides contextual weighting only - does not determine karma"
        }
        
        return weights
    
    def get_user_kundali(self, user_id: str) -> Optional[KundaliData]:
        """Get user's stored kundali"""
        if user_id in self.kundali_store:
            return self.kundali_store[user_id]['kundali']
        return None
    
    def does_not_override_karma(self, user_id: str, karma_result: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate that kundali does NOT override karma decisions"""
        # This method confirms that karma results remain unchanged
        # regardless of kundali readings
        contextual_weights = self.get_contextual_weighting(user_id)
        
        result = karma_result.copy()
        result['kundali_context'] = contextual_weights
        result['karma_decision_unaffected'] = True
        
        print(f"Kundali exists for user {user_id}: {bool(user_id in self.kundali_store)}")
        print(f"Kundali influence on karma: {contextual_weights.get('kundali_influence', 0)} (very low)")
        print(f"Karma decision remains: {result.get('karma_band', 'unknown')}")
        print("✓ Kundali does NOT override karma decision")
        
        return result


# Example usage and demonstration
def demonstrate_kundali_context():
    """Demonstrate Kundali context without overriding karma"""
    print("Vedic Astrology (Kundali) Context Layer")
    print("=" * 50)
    
    # Create context provider
    kundali_provider = KundaliContextProvider()
    
    # Example user with complete birth details
    user_id = "user_astro_123"
    dob = date(1990, 5, 15)
    tob = time(8, 30, 0)  # 8:30 AM
    
    print(f"Creating Kundali for user: {user_id}")
    print(f"DOB: {dob}, TOB: {tob}")
    
    # Create user's kundali
    kundali = kundali_provider.create_user_kundali(user_id, dob, tob)
    
    print(f"\nGenerated Kundali:")
    print(f"  Moon Sign: {kundali.moon_sign.value}")
    print(f"  Sun Sign: {kundali.sun_sign.value if kundali.sun_sign else 'Not calculated'}")
    print(f"  Ascendant: {kundali.ascendant.value if kundali.ascendant else 'Not calculated (TOB needed)'}")
    print(f"  Nakshatra: {kundali.nakshatra}")
    print(f"  Strength: {kundali.kundali_strength} (0.0-1.0)")
    print(f"  Partial: {kundali.partial}")
    
    # Example karma result
    karma_result = {
        "karma_score": 75.5,
        "karma_band": "positive",
        "details": "Based on user interactions and behavior"
    }
    
    print(f"\nOriginal karma result: {karma_result}")
    
    # Apply kundali context (without changing karma)
    contextual_result = kundali_provider.does_not_override_karma(user_id, karma_result)
    
    print(f"\nResult with Kundali Context: {contextual_result}")
    
    # Example with partial kundali (no TOB)
    print(f"\n" + "="*50)
    print("Testing Partial Kundali (no Time of Birth)...")
    
    user_id_partial = "user_partial_456"
    dob_partial = date(1985, 11, 22)
    
    kundali_partial = kundali_provider.create_user_kundali(user_id_partial, dob_partial)
    
    print(f"Partial Kundali for {user_id_partial}:")
    print(f"  Moon Sign: {kundali_partial.moon_sign.value}")
    print(f"  Strength: {kundali_partial.kundali_strength} (lower due to missing TOB)")
    print(f"  Partial: {kundali_partial.partial}")
    
    # Contextual weights for partial kundali
    weights = kundali_provider.get_contextual_weighting(user_id_partial)
    print(f"  Contextual weights: {weights}")


if __name__ == "__main__":
    demonstrate_kundali_context()