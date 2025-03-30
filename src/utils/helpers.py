from typing import Dict, List, Tuple
import logging
import json

def setup_logging(log_file: str = 'logs/fleet_logs.txt'):
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file
    )

def validate_nav_graph(nav_graph_data: Dict) -> bool:
    """Validate the structure of the navigation graph"""
    if 'levels' in nav_graph_data:
        if not isinstance(nav_graph_data['levels'], dict):
            return False
        if 'level1' not in nav_graph_data['levels']:
            return False
        level_data = nav_graph_data['levels']['level1']
    else:
        level_data = nav_graph_data
    
    required_keys = {'vertices', 'lanes'}
    if not all(key in level_data for key in required_keys):
        return False
    
    if not isinstance(level_data['vertices'], list):
        return False
        
    if not isinstance(level_data['lanes'], list):
        return False
        
    for lane in level_data['lanes']:
        if len(lane) < 2 or not all(isinstance(v, int) for v in lane[:2]):
            return False
            
    return True

def load_nav_graph(file_path: str) -> Dict:
    """Load and validate navigation graph from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if not validate_nav_graph(data):
        raise ValueError("Invalid navigation graph structure")
    
    return data