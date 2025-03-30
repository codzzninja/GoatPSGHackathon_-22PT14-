from typing import Dict, List, Set, Tuple
import logging

class TrafficManager:
    def __init__(self, nav_graph):
        self.nav_graph = nav_graph
        self.lane_occupancy: Dict[Tuple[int, int], int] = {}
        self.vertex_occupancy: Dict[int, int] = {}
        self.logger = logging.getLogger('TrafficManager')
        
    def request_lane(self, robot_id: int, from_vertex: int, to_vertex: int) -> bool:
        lane = self._normalize_lane(from_vertex, to_vertex)
        
        if lane in self.lane_occupancy:
            if self.lane_occupancy[lane] != robot_id:
                self.logger.debug(f"Lane {lane} occupied by {self.lane_occupancy[lane]}")
                return False
        self.lane_occupancy[lane] = robot_id
        return True
    
    def request_vertex(self, robot_id: int, vertex_id: int) -> bool:
        if vertex_id in self.vertex_occupancy:
            if self.vertex_occupancy[vertex_id] != robot_id:
                self.logger.debug(f"Vertex {vertex_id} occupied by {self.vertex_occupancy[vertex_id]}")
                return False
        self.vertex_occupancy[vertex_id] = robot_id
        return True
    
    def release_lane(self, robot_id: int, from_vertex: int, to_vertex: int):
        lane = self._normalize_lane(from_vertex, to_vertex)
        if lane in self.lane_occupancy and self.lane_occupancy[lane] == robot_id:
            del self.lane_occupancy[lane]
    
    def release_vertex(self, robot_id: int, vertex_id: int):
        if vertex_id in self.vertex_occupancy and self.vertex_occupancy[vertex_id] == robot_id:
            del self.vertex_occupancy[vertex_id]
    
    def _normalize_lane(self, from_vertex: int, to_vertex: int) -> Tuple[int, int]:
        return (min(from_vertex, to_vertex), max(from_vertex, to_vertex))
    
    def get_occupied_lanes(self) -> List[Tuple[int, int]]:
        return list(self.lane_occupancy.keys())
    
    def get_occupied_vertices(self) -> List[int]:
        return list(self.vertex_occupancy.keys())