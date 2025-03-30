from typing import Dict, List, Optional, Tuple
from ..models.robot import Robot, RobotStatus
from ..models.nav_graph import NavGraph
from ..controllers.traffic_manager import TrafficManager
import logging

class FleetManager:
    def __init__(self, nav_graph: NavGraph):
        self.nav_graph = nav_graph
        self.robots: Dict[int, Robot] = {}
        self.next_robot_id = 0
        self.traffic_manager = TrafficManager(nav_graph)
        self.logger = logging.getLogger('FleetManager')
        
    def spawn_robot(self, vertex_id: int) -> Optional[Robot]:
        """Spawn a new robot at the specified vertex"""
        if vertex_id < 0 or vertex_id >= len(self.nav_graph.vertices):
            self.logger.error(f"Invalid vertex ID {vertex_id} for spawning robot")
            return None
            
        if not self.traffic_manager.request_vertex(self.next_robot_id, vertex_id):
            self.logger.warning(f"Vertex {vertex_id} is occupied, cannot spawn robot")
            return None
            
        robot = Robot(self.next_robot_id, vertex_id, self.nav_graph)
        self.robots[self.next_robot_id] = robot
        self.next_robot_id += 1
        self.logger.info(f"Spawned robot {robot.id} at vertex {vertex_id}")
        return robot
    
    def assign_task(self, robot_id: int, destination_vertex: int) -> bool:
        """Assign a navigation task to a robot"""
        if robot_id not in self.robots:
            self.logger.error(f"Robot ID {robot_id} not found")
            return False
            
        robot = self.robots[robot_id]
        if robot.status == RobotStatus.CHARGING:
            self.logger.warning(f"Robot {robot_id} is charging and cannot be assigned tasks")
            return False

        occupied = self.traffic_manager.get_occupied_vertices()
        path = self.nav_graph.find_shortest_path(
            robot.current_vertex, 
            destination_vertex,
            occupied_vertices=occupied
        )
        
        if not path:
            self.logger.error(f"No valid path from {robot.current_vertex} to {destination_vertex}")
            return False
            
        if len(path) > 1:
            self.traffic_manager.release_vertex(robot.id, robot.current_vertex)
            
        robot.assign_task(destination_vertex, path)
        return True
    
    def update_robots(self, delta_time: float):
        """Update all robot positions with traffic management"""
        # Update moving robots first
        for robot in list(self.robots.values()):
            if robot.status == RobotStatus.MOVING and robot.path:
                self._process_movement(robot, delta_time)
        
        # Then check waiting robots
        for robot in list(self.robots.values()):
            if robot.status == RobotStatus.WAITING and robot.path:
                self._check_waiting_robot(robot)
    
    def _process_movement(self, robot: Robot, delta_time: float):
        """Handle movement logic for a single robot"""
        next_vertex = robot.path[0]
        
        if self._can_move_to(robot, next_vertex):
            robot.update_position(delta_time)
            
            if robot.current_vertex == next_vertex:
                self._handle_vertex_reached(robot, next_vertex)
        else:
            robot.status = RobotStatus.WAITING
    
    def _can_move_to(self, robot: Robot, next_vertex: int) -> bool:
        """Check if robot can move to next vertex"""
        # Allow staying at current position
        if next_vertex == robot.current_vertex:
            return True
            
        # Check vertex availability
        if not self.traffic_manager.request_vertex(robot.id, next_vertex):
            return False
            
        # Check lane availability
        if not self.traffic_manager.request_lane(robot.id, robot.current_vertex, next_vertex):
            return False
            
        return True
    
    def _handle_vertex_reached(self, robot: Robot, next_vertex: int):
        """Handle actions when robot reaches a vertex"""
        # Release previous resources immediately
        if robot.previous_vertex is not None:
            self.traffic_manager.release_lane(robot.id, robot.previous_vertex, robot.current_vertex)
            self.traffic_manager.release_vertex(robot.id, robot.previous_vertex)
        
        # Update path
        robot.path.pop(0)
        
        if not robot.path:
            robot.status = RobotStatus.TASK_COMPLETE
            self.traffic_manager.release_vertex(robot.id, robot.current_vertex)
    
    def _check_waiting_robot(self, robot: Robot):
        """Attempt to resume waiting robot with path recalculation"""
        occupied = self.traffic_manager.get_occupied_vertices()
        new_path = self.nav_graph.find_shortest_path(
            robot.current_vertex,
            robot.destination_vertex,
            occupied_vertices=occupied
        )
        
        if new_path:
            robot.path = new_path
            robot.status = RobotStatus.MOVING
            self.logger.info(f"Robot {robot.id} found new path to {robot.destination_vertex}")
    
    def get_robot_status(self, robot_id: int) -> Optional[str]:
        if robot_id not in self.robots:
            return None
        return self.robots[robot_id].status.name
    
    def get_robot_position(self, robot_id: int) -> Optional[Tuple[float, float]]:
        if robot_id not in self.robots:
            return None
        return self.robots[robot_id].get_position()
    
    def get_robot_color(self, robot_id: int) -> Optional[str]:
        if robot_id not in self.robots:
            return None
        return self.robots[robot_id].color
    
    def get_blocked_lanes(self) -> List[Tuple[int, int]]:
        return self.traffic_manager.get_occupied_lanes()
    
    def get_blocked_vertices(self) -> List[int]:
        return self.traffic_manager.get_occupied_vertices()