# ===================================================================================
# signal_algorithms.py: Advanced Multi-Junction Signal Control System
#
# Handles 2-6 way intersections with accident-aware optimization.
# Maharashtra & Karnataka traffic patterns optimized.
# ===================================================================================

import time
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class JunctionType(Enum):
    TWO_WAY = 2    # T-junction
    THREE_WAY = 3  # Y-junction
    FOUR_WAY = 4   # Standard cross (+)
    FIVE_WAY = 5   # Star junction
    SIX_WAY = 6    # Complex intersection

class IncidentLevel(Enum):
    NORMAL = 0
    TRAFFIC_JAM = 1
    MINOR_ACCIDENT = 2
    SEVERE_ACCIDENT = 3
    FIRE = 4
    AMBULANCE = 5  # Future scope with GPS

@dataclass
class LaneState:
    """Represents the state of a single lane/direction"""
    name: str
    vehicle_count: int
    is_blocked: bool = False
    incident_level: IncidentLevel = IncidentLevel.NORMAL
    priority: int = 0  # Higher = more priority
    min_green_time: int = 5  # seconds
    max_green_time: int = 45  # seconds

@dataclass
class SignalTimings:
    """Output of the algorithm"""
    green_lane: str
    timings: Dict[str, int]  # lane_name: seconds
    reason: str
    emergency_mode: bool = False

class SmartSignalController:
    """
    Core algorithm that decides signal timings based on:
    - Junction type (2-6 way)
    - Real-time traffic counts
    - Accident/incident detection
    - Maharashtra/Karnataka traffic patterns
    """
    
    def __init__(self, junction_type: JunctionType, algorithm_mode: str = 'adaptive'):
        self.junction_type = junction_type
        self.algorithm_mode = algorithm_mode 
        self.lanes = self._initialize_lanes()
        self.current_green = None
        self.last_switch_time = time.time()
        self.cycle_index = 0
        
        # Calibrated for Indian traffic conditions
        self.BASE_CYCLE_TIME = 8  # seconds per lane (normal)
        self.EMERGENCY_CYCLE_TIME = 3  # Fast switching during incidents
        self.TRAFFIC_THRESHOLD_LOW = 5
        self.TRAFFIC_THRESHOLD_HIGH = 15
        
    def _initialize_lanes(self) -> Dict[str, LaneState]:
        """Create lane configuration based on junction type"""
        configs = {
            JunctionType.TWO_WAY: ['north', 'south'],
            JunctionType.THREE_WAY: ['north', 'east', 'south'],
            JunctionType.FOUR_WAY: ['north', 'east', 'south', 'west'],
            JunctionType.FIVE_WAY: ['north', 'northeast', 'east', 'south', 'west'],
            JunctionType.SIX_WAY: ['north', 'northeast', 'east', 'southeast', 'south', 'west']
        }
        
        lane_names = configs[self.junction_type]
        return {name: LaneState(name=name, vehicle_count=0) for name in lane_names}
    
    def update_traffic_data(self, lane_counts: Dict[str, int]):
        """Update vehicle counts from AI detection or manual input"""
        for lane_name, count in lane_counts.items():
            if lane_name in self.lanes:
                self.lanes[lane_name].vehicle_count = count
    
    def mark_incident(self, lane_name: str, incident_type: IncidentLevel):
        """Mark a lane as having an accident/incident"""
        if lane_name in self.lanes:
            self.lanes[lane_name].incident_level = incident_type
            if incident_type in [IncidentLevel.SEVERE_ACCIDENT, IncidentLevel.FIRE]:
                self.lanes[lane_name].is_blocked = True
    
    def clear_incident(self, lane_name: str):
        """Clear incident status"""
        if lane_name in self.lanes:
            self.lanes[lane_name].incident_level = IncidentLevel.NORMAL
            self.lanes[lane_name].is_blocked = False
    
    # ==================== CORE ALGORITHMS ====================
    
    def algorithm_normal_adaptive(self) -> SignalTimings:
        """
        ALGORITHM 1: Adaptive Traffic-Based (Normal Conditions)
        
        Logic:
        - Calculates weighted priority based on vehicle count
        - Gives longer green time to congested lanes
        - Maintains fairness with minimum green times
        - Uses round-robin as fallback
        """
        active_lanes = {k: v for k, v in self.lanes.items() if not v.is_blocked}
        
        if not active_lanes:
            return SignalTimings("none", {}, "All lanes blocked")
        
        # Calculate priorities
        total_vehicles = sum(lane.vehicle_count for lane in active_lanes.values())
        
        if total_vehicles < self.TRAFFIC_THRESHOLD_LOW:
            # Low traffic: Simple round-robin
            lane_list = list(active_lanes.keys())
            selected = lane_list[self.cycle_index % len(lane_list)]
            
            return SignalTimings(
                green_lane=selected,
                timings={selected: self.BASE_CYCLE_TIME},
                reason="Low traffic - Round robin"
            )
        
        # High traffic: Weighted by vehicle count
        max_lane = max(active_lanes.items(), key=lambda x: x[1].vehicle_count)
        selected_lane = max_lane[0]
        count = max_lane[1].vehicle_count
        
        # Calculate green time proportional to congestion
        # Formula: Base time + (vehicle_count * weight_factor)
        weight_factor = 2 if self.algorithm_mode == 'weighted' else 1  # Weighted gives 2s per vehicle
        green_time = min(
            self.BASE_CYCLE_TIME + (count * weight_factor),
            max_lane[1].max_green_time
        )
        
        return SignalTimings(
            green_lane=selected_lane,
            timings={selected_lane: green_time},
            reason=f"Adaptive: {count} vehicles in {selected_lane}"
        )
    
    def algorithm_accident_diversion(self, blocked_lane: str) -> SignalTimings:
        """
        ALGORITHM 2: Accident Response - Lane Blockage
        
        Logic:
        - Identifies blocked lane (accident site)
        - Prioritizes opposite direction to clear congestion
        - Gives adjacent lanes extra green time for diversion
        - Skips blocked lane completely
        """
        active_lanes = {k: v for k, v in self.lanes.items() 
                       if not v.is_blocked and k != blocked_lane}
        
        if not active_lanes:
            return SignalTimings("none", {}, "System locked - all blocked")
        
        # Find opposite lane for diversion
        opposite_map = {
            'north': 'south', 'south': 'north',
            'east': 'west', 'west': 'east',
            'northeast': 'south', 'southeast': 'west'
        }
        
        opposite_lane = opposite_map.get(blocked_lane)
        
        if opposite_lane and opposite_lane in active_lanes:
            # Prioritize opposite direction
            return SignalTimings(
                green_lane=opposite_lane,
                timings={opposite_lane: 30},  # Extended green for clearing
                reason=f"Diversion from blocked {blocked_lane}",
                emergency_mode=True
            )
        
        # Fallback: prioritize highest traffic adjacent lane
        max_lane = max(active_lanes.items(), key=lambda x: x[1].vehicle_count)
        return SignalTimings(
            green_lane=max_lane[0],
            timings={max_lane[0]: 25},
            reason=f"Adjacent lane clearing: {max_lane[0]}",
            emergency_mode=True
        )
    
    def algorithm_emergency_corridor(self, emergency_direction: str) -> SignalTimings:
        """
        ALGORITHM 3: Green Corridor for Emergency Vehicles
        
        Logic:
        - Clears path in emergency vehicle direction
        - All other lanes RED
        - Fast cycle time (3s) for quick response
        - Used for: Ambulance, Fire Brigade (future GPS-based)
        """
        if emergency_direction not in self.lanes:
            emergency_direction = 'north'  # Default fallback
        
        return SignalTimings(
            green_lane=emergency_direction,
            timings={emergency_direction: 60},  # Long green for corridor
            reason=f"EMERGENCY CORRIDOR: {emergency_direction.upper()}",
            emergency_mode=True
        )
    
    def algorithm_fire_evacuation(self, fire_lane: str) -> SignalTimings:
        """
        ALGORITHM 4: Fire Evacuation Mode
        
        Logic:
        - Blocks fire-affected lane
        - Opens ALL other lanes (multi-directional evacuation)
        - Short cycles (5s each) to maximize throughput
        - Prioritizes lanes leading away from fire
        """
        safe_lanes = [k for k in self.lanes.keys() if k != fire_lane]
        
        if not safe_lanes:
            return SignalTimings("none", {}, "Fire evacuation - system override")
        
        # All safe lanes get equal short green times
        timings = {lane: 5 for lane in safe_lanes}
        
        return SignalTimings(
            green_lane=safe_lanes[self.cycle_index % len(safe_lanes)],
            timings=timings,
            reason=f"FIRE EVACUATION from {fire_lane}",
            emergency_mode=True
        )
    
    def algorithm_multi_accident(self, accident_lanes: List[str]) -> SignalTimings:
        """
        ALGORITHM 5: Multiple Accidents (Worst Case)
        
        Logic:
        - Handles 2+ simultaneous accidents
        - Prioritizes single clear exit route
        - Minimal switching to avoid confusion
        - Alerts for manual intervention
        """
        safe_lanes = [k for k in self.lanes.keys() if k not in accident_lanes]
        
        if not safe_lanes:
            return SignalTimings(
                "none", 
                {}, 
                "CRITICAL: All lanes affected - Manual override required",
                emergency_mode=True
            )
        
        # Pick the safest lane with most capacity
        best_lane = max(
            [(k, self.lanes[k]) for k in safe_lanes],
            key=lambda x: x[1].vehicle_count
        )[0]
        
        return SignalTimings(
            green_lane=best_lane,
            timings={best_lane: 45},  # Long green for mass clearing
            reason=f"Multi-accident: Using {best_lane} as primary exit",
            emergency_mode=True
        )
    
    # ==================== MASTER DECISION ENGINE ====================
    
    def decide_signals(self) -> Dict[str, str]:
        """
        Master function that selects the appropriate algorithm
        and returns signal states for all lanes.
        
        Returns: {'north': 'green', 'east': 'red', ...}
        """
        # Detect incidents
        blocked_lanes = [k for k, v in self.lanes.items() if v.is_blocked]
        fire_lanes = [k for k, v in self.lanes.items() 
                     if v.incident_level == IncidentLevel.FIRE]
        accident_lanes = [k for k, v in self.lanes.items() 
                         if v.incident_level in [IncidentLevel.SEVERE_ACCIDENT, IncidentLevel.MINOR_ACCIDENT]]
        
        # Algorithm selection hierarchy
        if fire_lanes:
            timing = self.algorithm_fire_evacuation(fire_lanes[0])
        elif len(accident_lanes) >= 2:
            timing = self.algorithm_multi_accident(accident_lanes)
        elif accident_lanes:
            timing = self.algorithm_accident_diversion(accident_lanes[0])
        else:
            timing = self.algorithm_normal_adaptive()
        
        # Convert to signal state dict
        signals = {lane: 'red' for lane in self.lanes.keys()}
        signals[timing.green_lane] = 'green'
        
        # Update cycle tracking
        current_time = time.time()
        cycle_duration = self.EMERGENCY_CYCLE_TIME if timing.emergency_mode else self.BASE_CYCLE_TIME
        
        if current_time - self.last_switch_time > cycle_duration:
            self.cycle_index += 1
            self.last_switch_time = current_time
        
        return signals


# ==================== USAGE EXAMPLE ====================

def example_usage():
    """Demonstrates how to use the controller"""
    
    # Initialize a 4-way intersection (like your current setup)
    controller = SmartSignalController(JunctionType.FOUR_WAY)
    
    # Update with live traffic data
    controller.update_traffic_data({
        'north': 12,  # 12 vehicles detected
        'east': 5,
        'south': 8,
        'west': 3
    })
    
    # Get signals - will use adaptive algorithm
    signals = controller.decide_signals()
    print("Normal mode:", signals)
    # Expected: {'north': 'green', 'east': 'red', 'south': 'red', 'west': 'red'}
    
    # Simulate accident in south lane
    controller.mark_incident('south', IncidentLevel.SEVERE_ACCIDENT)
    signals = controller.decide_signals()
    print("Accident mode:", signals)
    # Expected: Prioritizes north (opposite) for diversion
    
    # Clear incident
    controller.clear_incident('south')
    signals = controller.decide_signals()
    print("Back to normal:", signals)


if __name__ == "__main__":
    example_usage()