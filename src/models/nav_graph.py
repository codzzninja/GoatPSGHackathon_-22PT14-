import json
from typing import Dict, List, Optional, Tuple

class NavGraph:
    def __init__(self, file_path: str):
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'levels' in data:
            level_data = data['levels']['level1']
            self.vertices = level_data['vertices']
            self.lanes = level_data['lanes']
        else:
            self.vertices = data['vertices']
            self.lanes = data['lanes']
            
        self.adjacency_list = self._build_adjacency_list()
        self.lane_properties = self._extract_lane_properties()
        
    def _build_adjacency_list(self) -> Dict[int, List[int]]:
        adj_list = {i: [] for i in range(len(self.vertices))}
        for lane in self.lanes:
            adj_list[lane[0]].append(lane[1])
            adj_list[lane[1]].append(lane[0])
        return adj_list
    
    def _extract_lane_properties(self) -> Dict[Tuple[int, int], Dict]:
        properties = {}
        for lane in self.lanes:
            from_idx, to_idx = lane[0], lane[1]
            props = lane[2] if len(lane) > 2 else {}
            properties[(from_idx, to_idx)] = props
            properties[(to_idx, from_idx)] = props
        return properties
    
    def get_vertex_position(self, vertex_id: int) -> Tuple[float, float]:
        return (self.vertices[vertex_id][0], self.vertices[vertex_id][1])
    
    def get_vertex_name(self, vertex_id: int) -> str:
        return self.vertices[vertex_id][2].get('name', f'V{vertex_id}')
    
    def is_charger(self, vertex_id: int) -> bool:
        return self.vertices[vertex_id][2].get('is_charger', False)
    
    def get_lane_speed_limit(self, from_vertex: int, to_vertex: int) -> float:
        return self.lane_properties.get((from_vertex, to_vertex), {}).get('speed_limit', 0)
    
    def find_shortest_path(self, start: int, end: int, occupied_vertices: List[int] = None) -> Optional[List[int]]:
        """Find shortest path using BFS while avoiding occupied vertices"""
        if start == end:
            return [start]
        
        visited = {start: None}
        queue = [start]
        occupied = set(occupied_vertices) if occupied_vertices else set()
        
        while queue:
            current = queue.pop(0)
            
            for neighbor in self.adjacency_list[current]:
                if neighbor in occupied or neighbor == current:
                    continue
                    
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)
                    
                    if neighbor == end:
                        path = []
                        while neighbor is not None:
                            path.append(neighbor)
                            neighbor = visited[neighbor]
                        return path[::-1]
        return None