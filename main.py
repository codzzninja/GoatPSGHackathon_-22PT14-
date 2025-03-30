import tkinter as tk
from src.gui.fleet_gui import FleetGUI
import os
import logging

def main():
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Initialize GUI
    root = tk.Tk()
    app = FleetGUI(root, 'data/nav_graph_1.json')
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()