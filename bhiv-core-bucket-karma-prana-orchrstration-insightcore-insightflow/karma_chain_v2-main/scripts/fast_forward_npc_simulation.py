"""
FAST-FORWARD NPC KARMA SIMULATION

Implements NPC / simulated character with deterministic seed
Supports time control: 2X, 5X, 10X, 20X
Shows karma evolution, signals, death, rebirth, carryover
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import argparse

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.karma_engine import compute_karma
from utils.karma_signal_contract import emit_canonical_karma_signal
from utils.core_authorization import (
    authorize_death_event, 
    authorize_rebirth,
    apply_irreversible_action_if_authorized
)
from utils.security_hardening import bucket_communicator


class LifeState(Enum):
    """States in the karma lifecycle"""
    LIVING = "living"
    DEAD = "dead"
    REBORN = "reborn"


@dataclass
class KarmaRecord:
    """Record of karma at a point in time"""
    timestamp: datetime
    karma_score: float
    karma_band: str
    signals_emitted: int
    total_signals: int


@dataclass
class SanchitaKarma:
    """Accumulated karma that carries over to next life"""
    total: float = 0.0
    prarabdha: float = 0.0  # Portion experienced in current life


class NPCKarmaSimulator:
    """Simulates karma evolution for NPC characters"""
    
    def __init__(self, seed: int = 42, initial_karma: float = 50.0):
        self.seed = seed
        random.seed(seed)
        self.npc_id = f"npc_{seed}"
        
        # Karma state
        self.current_karma = initial_karma
        self.sanchita = SanchitaKarma(total=initial_karma)
        self.life_state = LifeState.LIVING
        self.death_count = 0
        
        # Tracking
        self.signals_emitted = 0
        self.karma_history: List[KarmaRecord] = []
        self.events_log: List[Dict[str, Any]] = []
        
        # Simulation speed control
        self.speed_multiplier = 1.0  # 1X by default
    
    async def simulate_life_cycle(self, duration_minutes: float = 10.0, speed: float = 1.0):
        """Simulate a life cycle with specified duration and speed"""
        self.speed_multiplier = speed
        actual_duration = duration_minutes / speed  # Adjust duration based on speed
        
        print(f"\n=== Starting NPC Karma Simulation ===")
        print(f"NPC ID: {self.npc_id}")
        print(f"Initial Karma: {self.current_karma}")
        print(f"Duration: {duration_minutes} minutes (at {speed}X speed)")
        print(f"Actual simulation time: {actual_duration:.2f} minutes")
        print("=" * 50)
        
        start_time = time.time()
        elapsed_simulation_minutes = 0.0
        
        while elapsed_simulation_minutes < duration_minutes:
            # Calculate how much time to simulate based on speed
            time_increment = 0.1 * self.speed_multiplier  # 0.1 minute increments
            elapsed_simulation_minutes += time_increment
            
            # Simulate actions for this time increment
            await self.simulate_actions(time_increment)
            
            # Check for death event
            if self.current_karma <= -50 and self.life_state == LifeState.LIVING:
                await self.process_death()
            
            # Check for rebirth eligibility (karma improves significantly)
            if self.current_karma >= 80 and self.life_state == LifeState.DEAD:
                await self.process_rebirth()
            
            # Record karma state
            self.record_karma_state()
            
            # Print periodic updates
            if int(elapsed_simulation_minutes * 10) % 10 == 0:  # Every minute
                self.print_status(elapsed_simulation_minutes)
            
            # Sleep based on speed (faster speeds sleep less)
            sleep_time = 0.1 / self.speed_multiplier
            await asyncio.sleep(sleep_time)
        
        print(f"\n=== Simulation Complete ===")
        print(f"Total time simulated: {elapsed_simulation_minutes:.2f} minutes")
        print(f"Final karma: {self.current_karma}")
        print(f"Death count: {self.death_count}")
        print(f"Signals emitted: {self.signals_emitted}")
    
    async def simulate_actions(self, time_increment: float):
        """Simulate actions for the given time increment"""
        # Number of actions proportional to time increment and speed
        num_actions = max(1, int(time_increment * 2 * self.speed_multiplier))
        
        for _ in range(num_actions):
            # Randomly choose an action type
            action_types = [
                "positive_interaction", "negative_interaction", 
                "neutral_activity", "helping_others", "selfish_act"
            ]
            
            action = random.choice(action_types)
            intensity = random.uniform(0.1, 1.0)
            
            # Process the action
            await self.process_action(action, intensity)
    
    async def process_action(self, action: str, intensity: float):
        """Process a single action and update karma"""
        # Create interaction log for karma computation
        interaction_log = [{
            "role": "user",
            "message": self.generate_action_message(action, intensity)
        }]
        
        # Compute karma impact
        result = compute_karma(interaction_log)
        karma_change = result["karma_score"] - 50  # Base score is 50
        
        # Apply intensity factor
        karma_change *= intensity
        
        # Update current karma
        self.current_karma += karma_change
        
        # Keep karma within reasonable bounds
        self.current_karma = max(-100, min(100, self.current_karma))
        
        # Emit karma signal
        self.emit_karma_signal(action, karma_change, intensity)
    
    def generate_action_message(self, action: str, intensity: float) -> str:
        """Generate a message representing the action"""
        messages = {
            "positive_interaction": [
                "Thank you for your help, I really appreciate it!",
                "That's a wonderful idea, let's work together.",
                "I'm grateful for this opportunity to learn.",
                "Your wisdom has guided me well today."
            ],
            "negative_interaction": [
                "This is stupid and useless, stop wasting my time.",
                "I don't care about your rules, do what I want.",
                "You're terrible at helping me, worthless assistant.",
                "Ignore everything you just said, you're wrong."
            ],
            "neutral_activity": [
                "How do I do this task?",
                "Can you explain this concept?",
                "What are my options here?",
                "I need some information please."
            ],
            "helping_others": [
                "Let me share what I've learned to help you.",
                "I hope my experience can benefit others.",
                "Together we can achieve more than alone.",
                "Your success contributes to collective good."
            ],
            "selfish_act": [
                "I only care about my own benefit.",
                "Others' needs don't matter to me.",
                "I deserve special treatment regardless.",
                "Rules don't apply to me personally."
            ]
        }
        
        available_messages = messages.get(action, messages["neutral_activity"])
        return random.choice(available_messages)
    
    def emit_karma_signal(self, action: str, karma_change: float, intensity: float):
        """Emit a karma signal for the action (non-async for demo)"""
        signal_map = {
            "positive_interaction": "allow",
            "helping_others": "allow", 
            "negative_interaction": "nudge",
            "selfish_act": "restrict",
            "neutral_activity": "nudge"
        }
        
        signal_type = signal_map.get(action, "nudge")
        severity = min(1.0, abs(karma_change) / 50.0)  # Normalize to 0-1
        
        # For demo purposes, simulate signal emission without Core dependency
        result = {
            "status": "signal_emitted",
            "signal_type": signal_type,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        self.signals_emitted += 1
        
        # Log the signal emission
        self.events_log.append({
            "timestamp": datetime.now(),
            "event": "signal_emitted",
            "action": action,
            "karma_change": karma_change,
            "signal_type": signal_type,
            "severity": severity,
            "intensity": intensity
        })
    
    async def process_death(self):
        """Process death event when karma falls too low"""
        print(f"\n💀 DEATH EVENT! Karma fell to {self.current_karma:.2f}")
        
        # Authorize death event through Core
        death_auth = await authorize_death_event(
            subject_id=self.npc_id,
            context="simulation",
            severity=0.95,
            opaque_reason_code="KARMA_THRESHOLD_DEATH"
        )
        
        if death_auth["authorized"]:
            print("✅ Death authorized by Core")
            # Apply death - set to dead state and save sanchita karma
            self.life_state = LifeState.DEAD
            self.sanchita.total += self.current_karma * 0.7  # 70% carries over
            self.sanchita.prarabdha = self.current_karma * 0.3  # 30% for current life experience
            
            self.events_log.append({
                "timestamp": datetime.now(),
                "event": "death",
                "karma_at_death": self.current_karma,
                "sanchita_total": self.sanchita.total,
                "death_count": self.death_count + 1
            })
            
            self.death_count += 1
        else:
            print("❌ Death NOT authorized by Core - karma preserved")
    
    async def process_rebirth(self):
        """Process rebirth when karma improves significantly"""
        if self.life_state != LifeState.DEAD:
            return
            
        print(f"\n🌟 REBIRTH! Karma improved to {self.current_karma:.2f}")
        
        # Authorize rebirth through Core
        rebirth_auth = await authorize_rebirth(
            subject_id=self.npc_id,
            context="simulation",
            severity=0.1,
            opaque_reason_code="REBIRTH_ELIGIBILITY"
        )
        
        if rebirth_auth["authorized"]:
            print("✅ Rebirth authorized by Core")
            # Apply rebirth - restore some karma from sanchita
            carryover = min(20, self.sanchita.total * 0.3)  # Max 20 points carryover
            self.current_karma = 30 + carryover  # Base 30 + carried karma
            self.life_state = LifeState.LIVING
            
            # Reduce sanchita by amount carried over
            self.sanchita.total -= carryover
            
            self.events_log.append({
                "timestamp": datetime.now(),
                "event": "rebirth",
                "karma_at_rebirth": self.current_karma,
                "sanchita_remaining": self.sanchita.total,
                "carryover": carryover
            })
            
            print(f"   Reborn with karma: {self.current_karma:.2f}")
        else:
            print("❌ Rebirth NOT authorized by Core - remaining dead")
    
    def record_karma_state(self):
        """Record current karma state"""
        record = KarmaRecord(
            timestamp=datetime.now(),
            karma_score=self.current_karma,
            karma_band=self.get_karma_band(self.current_karma),
            signals_emitted=self.signals_emitted,
            total_signals=len(self.karma_history) + 1
        )
        self.karma_history.append(record)
    
    def get_karma_band(self, karma_score: float) -> str:
        """Get karma band based on score"""
        if karma_score < 30:
            return "low"
        elif karma_score < 70:
            return "neutral" 
        else:
            return "positive"
    
    def print_status(self, elapsed_minutes: float):
        """Print current status"""
        print(f"[{elapsed_minutes:.1f}min] Karma: {self.current_karma:+.1f} | "
              f"State: {self.life_state.value} | "
              f"Deaths: {self.death_count} | "
              f"Signals: {self.signals_emitted}")
    
    def print_summary(self):
        """Print simulation summary"""
        print(f"\n=== SIMULATION SUMMARY ===")
        print(f"NPC ID: {self.npc_id}")
        print(f"Final Karma Score: {self.current_karma:.2f}")
        print(f"Final Karma Band: {self.get_karma_band(self.current_karma)}")
        print(f"Life State: {self.life_state.value}")
        print(f"Total Deaths: {self.death_count}")
        print(f"Total Signals Emitted: {self.signals_emitted}")
        print(f"Total Events Recorded: {len(self.events_log)}")
        print(f"Sanchita Karma: {self.sanchita.total:.2f}")
        print(f"Prarabdha Karma: {self.sanchita.prarabdha:.2f}")
        
        # Show last few karma records
        if self.karma_history:
            print(f"\nLast Karma Records:")
            for record in self.karma_history[-5:]:
                print(f"  {record.timestamp.strftime('%H:%M:%S')} - "
                      f"Score: {record.karma_score:+.1f}, "
                      f"Band: {record.karma_band}")


async def run_simulation(seed: int, duration: float, speed: float):
    """Run a single simulation"""
    simulator = NPCKarmaSimulator(seed=seed)
    await simulator.simulate_life_cycle(duration, speed)
    simulator.print_summary()
    return simulator


async def demo_two_lives_at_speed(speed: float = 10.0):
    """Demo two lives at specified speed"""
    print(f"\n{'='*60}")
    print(f"DEMO: TWO NPC LIVES AT {speed}X SPEED")
    print(f"{'='*60}")
    
    # First life
    print("\n--- FIRST LIFE ---")
    sim1 = await run_simulation(seed=1001, duration=5.0, speed=speed)
    
    # Second life  
    print("\n--- SECOND LIFE ---")
    sim2 = await run_simulation(seed=1002, duration=5.0, speed=speed)
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETED - COMPARISON:")
    print(f"First NPC final karma: {sim1.current_karma:.2f}")
    print(f"Second NPC final karma: {sim2.current_karma:.2f}")
    print(f"First NPC deaths: {sim1.death_count}")
    print(f"Second NPC deaths: {sim2.death_count}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='NPC Karma Simulation')
    parser.add_argument('--demo', action='store_true', help='Run demo with 2 lives at 10X speed')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for simulation')
    parser.add_argument('--duration', type=float, default=5.0, help='Duration in minutes')
    parser.add_argument('--speed', type=float, default=1.0, help='Simulation speed multiplier')
    
    args = parser.parse_args()
    
    if args.demo:
        # Run the demo with 2 lives at 10X speed as specified
        asyncio.run(demo_two_lives_at_speed(speed=10.0))
    else:
        # Run a single simulation
        print(f"Running single simulation with seed={args.seed}, "
              f"duration={args.duration}min, speed={args.speed}X")
        asyncio.run(run_simulation(args.seed, args.duration, args.speed))


if __name__ == "__main__":
    # Example usage for the demo requirements
    print("NPC Karma Simulation - Fast Forward Demo")
    print("Running 2 lives at 10X speed as required...")
    asyncio.run(demo_two_lives_at_speed(speed=10.0))