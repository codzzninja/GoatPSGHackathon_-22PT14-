from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import time
import logging
import math

class RobotStatus(Enum):
    IDLE = auto()
    MOVING = auto()
    WAITING = auto()
    CHARGING = auto()
    TASK_COMPLETE = auto()

class Robot:
    def __init__(self, robot_id: int, start_vertex: int, nav_graph):
        self.id = robot_id
        self.current_vertex = start_vertex
        self.previous_vertex: Optional[int] = None
        self.destination_vertex: Optional[int] = None
        self.path: List[int] = []
        self.status = RobotStatus.IDLE
        self.speed = 1.0  # units per second
        self.progress = 0.0  # progress along current lane (0-1)
        self.color = self._generate_color(robot_id)
        self.logger = logging.getLogger(f'Robot_{robot_id}')
        self.nav_graph = nav_graph
        
    def _generate_color(self, robot_id: int) -> str:
        """Generate a unique color based on robot ID"""
        colors = ['#FF0000', '#0000FF', '#00FF00', '#FFA500', '#800080', 
                 '#00FFFF', '#FF00FF', '#A52A2A', '#008000', '#000080']
        return colors[robot_id % len(colors)]
    
    def assign_task(self, destination: int, path: List[int]):
        self.destination_vertex = destination
        self.path = path
        self.status = RobotStatus.MOVING
        self.progress = 0.0
        self.logger.info(f"Assigned task: moving to {destination} via path {path}")
        
    def update_position(self, delta_time: float) -> bool:
        """Update robot position. Returns True if position changed."""
        if self.status != RobotStatus.MOVING or not self.path:
            return False
            
        next_vertex = self.path[0]
        
        # Get speed limit for current lane (0 means no limit)
        speed_limit = self.nav_graph.get_lane_speed_limit(self.current_vertex, next_vertex)
        effective_speed = self.speed if speed_limit == 0 else min(self.speed, speed_limit)
        
        distance = delta_time * effective_speed
        remaining_distance = (1.0 - self.progress) * self._distance_to_next()
        
        if distance >= remaining_distance:
            # Move to next vertex
            self.previous_vertex = self.current_vertex
            self.current_vertex = next_vertex
            self.progress = 0.0
            self.logger.debug(f"Reached vertex {self.current_vertex}")
            return True
        else:
            # Move along current lane
            self.progress += distance / self._distance_to_next()
            return True
    
    def _distance_to_next(self) -> float:
        """Calculate actual distance to next vertex in path"""
        if not self.path:
            return 0.0
            
        start_pos = self.nav_graph.get_vertex_position(self.current_vertex)
        end_pos = self.nav_graph.get_vertex_position(self.path[0])
        return math.sqrt((end_pos[0]-start_pos[0])**2 + (end_pos[1]-start_pos[1])**2)
    
    def get_position(self) -> Tuple[float, float]:
        """Get current interpolated position"""
        if not self.path or self.status == RobotStatus.TASK_COMPLETE:
            return self.nav_graph.get_vertex_position(self.current_vertex)
            
        start_pos = self.nav_graph.get_vertex_position(self.current_vertex)
        end_pos = self.nav_graph.get_vertex_position(self.path[0])
        
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * self.progress
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * self.progress
        return (x, y)
    
    def charge(self):
        if self.status == RobotStatus.IDLE:
            self.status = RobotStatus.CHARGING
            self.logger.info("Started charging")
    
    def stop_charging(self):
        if self.status == RobotStatus.CHARGING:
            self.status = RobotStatus.IDLE
            self.logger.info("Stopped charging")