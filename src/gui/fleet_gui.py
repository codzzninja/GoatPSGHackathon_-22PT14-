import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Optional, Tuple
from ..models.nav_graph import NavGraph
from ..models.robot import Robot, RobotStatus
from ..controllers.fleet_manager import FleetManager
import logging
import time
import math
from PIL import Image, ImageTk
import os

class FleetGUI:
    def __init__(self, root: tk.Tk, nav_graph_file: str):
        self.root = root
        self.root.title("Fleet Management System")
        self.root.state('zoomed')  # Start maximized
        
        # Theme variables
        self.dark_mode = False
        self.theme = {
            'bg': '#f5f5f5',
            'fg': '#333333',
            'panel_bg': '#ffffff',
            'text_bg': '#ffffff',
            'text_fg': '#333333',
            'button_bg': '#e1e1e1',
            'button_fg': '#333333',
            'button_active_bg': '#0066ff',
            'button_active_fg': '#ffffff',
            'highlight': '#0066ff',
            'grid': '#f0f0f0',
            'lane': '#aaaaaa',
            'lane_speed': '#ff9933',
            'vertex': '#3399ff',
            'vertex_outline': '#0066cc',
            'charger': '#66cc00',
            'charger_outline': '#ffcc00',
            'selection': 'yellow',
            'blocked': '#ff3333',
            'console_bg': '#ffffff',
            'console_fg': '#333333',
            'status_legend_moving': 'blue',
            'status_legend_waiting': 'orange',
            'status_legend_charging': 'green'
        }
        
        # Initialize models and controllers
        self.nav_graph = NavGraph(nav_graph_file)
        self.fleet_manager = FleetManager(self.nav_graph)
        
        # GUI state
        self.selected_robot: Optional[int] = None
        self.selected_vertex: Optional[int] = None
        self.robot_colors: Dict[int, str] = {}
        self.robot_images: Dict[int, ImageTk.PhotoImage] = {}
        self.animation_queue = []
        
        # Setup logging
        self.setup_logging()
        
        # Load icons
        self.load_icons()
        
        # Create GUI components
        self.create_widgets()
        
        # Initialize scaling factors
        self.scale_factor = 1.0
        self.x_offset = 0
        self.y_offset = 0
        
        # Calculate the required canvas size based on the navigation graph
        self.calculate_canvas_size()
        
        # Draw the environment
        self.draw_environment()
        
        # Start update loop
        self.last_update_time = time.time()
        self.update()

    def toggle_dark_mode(self):
        """Switch between light and dark mode"""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            # Dark theme colors
            self.theme = {
                'bg': '#2d2d2d',
                'fg': '#e0e0e0',
                'panel_bg': '#3d3d3d',
                'text_bg': '#3d3d3d',
                'text_fg': '#e0e0e0',
                'button_bg': '#4d4d4d',
                'button_fg': '#e0e0e0',
                'button_active_bg': '#0066cc',
                'button_active_fg': '#ffffff',
                'highlight': '#0066cc',
                'grid': '#252525',
                'lane': '#555555',
                'lane_speed': '#cc7a00',
                'vertex': '#006699',
                'vertex_outline': '#004d99',
                'charger': '#339900',
                'charger_outline': '#ffcc00',
                'selection': '#ffff00',
                'blocked': '#cc0000',
                'console_bg': '#3d3d3d',
                'console_fg': '#e0e0e0',
                'status_legend_moving': '#4da6ff',
                'status_legend_waiting': '#ffb84d',
                'status_legend_charging': '#5cd65c'
            }
            self.dark_mode_btn.config(text='☀️ Light Mode')
        else:
            # Light theme colors
            self.theme = {
                'bg': '#f5f5f5',
                'fg': '#333333',
                'panel_bg': '#ffffff',
                'text_bg': '#ffffff',
                'text_fg': '#333333',
                'button_bg': '#e1e1e1',
                'button_fg': '#333333',
                'button_active_bg': '#0066ff',
                'button_active_fg': '#ffffff',
                'highlight': '#0066ff',
                'grid': '#f0f0f0',
                'lane': '#aaaaaa',
                'lane_speed': '#ff9933',
                'vertex': '#3399ff',
                'vertex_outline': '#0066cc',
                'charger': '#66cc00',
                'charger_outline': '#ffcc00',
                'selection': 'yellow',
                'blocked': '#ff3333',
                'console_bg': '#ffffff',
                'console_fg': '#333333',
                'status_legend_moving': 'blue',
                'status_legend_waiting': 'orange',
                'status_legend_charging': 'green'
            }
            self.dark_mode_btn.config(text='🌙 Dark Mode')
        
        # Apply theme to all widgets
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme to all widgets"""
        # Main window
        self.root.config(bg=self.theme['bg'])
        
        # Canvas
        self.canvas.config(bg=self.theme['panel_bg'])
        
        # Control frames
        for frame in [self.control_frame, self.status_frame]:
            frame.config(style='Panel.TFrame')
        
        # Text console
        self.info_text.config(
            bg=self.theme['console_bg'],
            fg=self.theme['console_fg'],
            insertbackground=self.theme['console_fg'],
            selectbackground=self.theme['highlight'],
            selectforeground='white'
        )
        
        # Labels
        for label in [self.status_label, self.robot_count_label]:
            label.config(foreground=self.theme['fg'])
        
        # Update status legend colors
        for child in self.status_indicators.winfo_children():
            if "Moving →" in child.cget("text"):
                child.config(foreground=self.theme['status_legend_moving'])
            elif "Waiting ⏳" in child.cget("text"):
                child.config(foreground=self.theme['status_legend_waiting'])
            elif "Charging ⚡" in child.cget("text"):
                child.config(foreground=self.theme['status_legend_charging'])
            else:
                child.config(foreground=self.theme['fg'])
        
        # Redraw everything
        self.draw_environment()

    def setup_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        
        # Configure main window background
        style.configure('TFrame', background=self.theme['bg'])
        
        # Configure panels
        style.configure('Panel.TFrame', 
                      background=self.theme['panel_bg'], 
                      relief=tk.RAISED, 
                      borderwidth=1)
        style.configure('Panel.TLabelframe', 
                       background=self.theme['panel_bg'], 
                       relief=tk.RAISED, 
                       borderwidth=1)
        style.configure('Panel.TLabelframe.Label', 
                      background=self.theme['panel_bg'], 
                      font=('Segoe UI', 10, 'bold'),
                      foreground=self.theme['fg'])
        
        # Configure buttons
        style.configure('TButton', 
                      font=('Segoe UI', 10), 
                      padding=6,
                      background=self.theme['button_bg'],
                      foreground=self.theme['button_fg'])
        style.map('TButton',
                 foreground=[('pressed', self.theme['button_active_fg']), 
                            ('active', self.theme['button_active_fg'])],
                 background=[('pressed', self.theme['button_active_bg']), 
                            ('active', self.theme['button_active_bg'])])
        
        # Configure labels
        style.configure('TLabel', 
                      background=self.theme['bg'], 
                      font=('Segoe UI', 10),
                      foreground=self.theme['fg'])
        style.configure('Title.TLabel', 
                      font=('Segoe UI', 12, 'bold'),
                      foreground=self.theme['fg'])
        
        # Configure scrollbar
        style.configure('TScrollbar', 
                      gripcount=0, 
                      background=self.theme['button_bg'], 
                      troughcolor=self.theme['bg'],
                      bordercolor=self.theme['bg'],
                      arrowcolor=self.theme['fg'], 
                      lightcolor=self.theme['bg'])

    def load_icons(self):
        """Load and prepare icons for the GUI"""
        try:
            # Create icons directory if it doesn't exist
            os.makedirs('assets/icons', exist_ok=True)
            
            # Robot icons (we'll generate these programmatically)
            self.icons = {
                'charger': self.create_icon('⚡', self.theme['charger'], 16),
                'warning': self.create_icon('⚠', '#FF0000', 16),
                'success': self.create_icon('✓', '#00AA00', 16),
                'robot': self.create_icon('R', '#FFFFFF', 14),
                'pause': self.create_icon('⏸', '#FFFFFF', 14),
                'play': self.create_icon('▶', '#FFFFFF', 14)
            }
        except Exception as e:
            self.logger.error(f"Error loading icons: {e}")
            self.icons = {}

    def create_icon(self, text, bg_color, font_size):
        """Create a simple icon from text"""
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create a small image
        size = (24, 24)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw circle background
        draw.ellipse((0, 0, size[0]-1, size[1]-1), fill=bg_color)
        
        # Draw text
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        text_width, text_height = draw.textsize(text, font=font)
        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2 - 2)
        
        draw.text(position, text, fill='white', font=font)
        
        # Convert to PhotoImage
        return ImageTk.PhotoImage(image)

    def calculate_canvas_size(self):
        """Calculate the required canvas size based on the navigation graph"""
        if not self.nav_graph.vertices:
            return
            
        # Find min/max coordinates
        x_coords = [v[0] for v in self.nav_graph.vertices]
        y_coords = [v[1] for v in self.nav_graph.vertices]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Add 20% padding around the environment
        padding = 0.2 * max(max_x - min_x, max_y - min_y)
        
        # Calculate canvas dimensions needed to fit the environment
        canvas_width = (max_x - min_x + 2 * padding) * 1.1  # Additional scaling
        canvas_height = (max_y - min_y + 2 * padding) * 1.1
        
        # Set the scroll region to accommodate the entire environment
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Calculate scaling factors to fit the environment in the visible area
        self.calculate_scaling_factors()

    def calculate_scaling_factors(self):
        """Calculate scaling factors to fit the map to the visible canvas area"""
        if not self.nav_graph.vertices:
            return
            
        # Get visible canvas dimensions (accounting for current zoom/scroll)
        visible_width = self.canvas.winfo_width()
        visible_height = self.canvas.winfo_height()
        
        if visible_width <= 1 or visible_height <= 1:  # Canvas not yet rendered
            return
            
        # Find min/max coordinates
        x_coords = [v[0] for v in self.nav_graph.vertices]
        y_coords = [v[1] for v in self.nav_graph.vertices]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Add 10% padding
        padding_x = (max_x - min_x) * 0.1
        padding_y = (max_y - min_y) * 0.1
        
        # Calculate required scaling
        x_scale = visible_width / (max_x - min_x + 2 * padding_x)
        y_scale = visible_height / (max_y - min_y + 2 * padding_y)
        
        # Use the smaller scale to maintain aspect ratio
        self.scale_factor = min(x_scale, y_scale)
        
        # Calculate offsets to center the map
        self.x_offset = -min_x * self.scale_factor + (visible_width - (max_x - min_x) * self.scale_factor) / 2
        self.y_offset = -min_y * self.scale_factor + (visible_height - (max_y - min_y) * self.scale_factor) / 2

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='logs/fleet_logs.txt'
        )
        self.logger = logging.getLogger('FleetGUI')

    def create_widgets(self):
        # Setup styles first
        self.setup_styles()
        
        # Configure root window background
        self.root.configure(background=self.theme['bg'])
        
        # Main paned window for resizable panels
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Visualization with Scrollbars
        left_frame = ttk.Frame(main_pane, style='Panel.TFrame')
        main_pane.add(left_frame, weight=3)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(left_frame, bg=self.theme['panel_bg'], bd=0, highlightthickness=0)
        
        h_scroll = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        
        # Grid layout for scrollable canvas
        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        
        # Configure canvas to expand with window
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Right panel - Controls and information
        right_frame = ttk.Frame(main_pane, style='Panel.TFrame')
        main_pane.add(right_frame, weight=1)
        
        # Control panel
        self.control_frame = ttk.LabelFrame(right_frame, text="🚀 Robot Controls", style='Panel.TLabelframe', padding=10)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Dark mode toggle button
        self.dark_mode_btn = ttk.Button(self.control_frame, 
                                      text='🌙 Dark Mode' if not self.dark_mode else '☀️ Light Mode',
                                      command=self.toggle_dark_mode)
        self.dark_mode_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Robot management buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        spawn_btn = ttk.Button(btn_frame, text="➕ Spawn Robot", command=self.spawn_robot)
        spawn_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        task_btn = ttk.Button(btn_frame, text="🎯 Assign Task", command=self.assign_task)
        task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        charge_btn = ttk.Button(btn_frame, text="⚡ Charge Robot", command=self.charge_robot)
        charge_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        btn_frame2 = ttk.Frame(self.control_frame)
        btn_frame2.pack(fill=tk.X, pady=(0, 5))
        
        pause_btn = ttk.Button(btn_frame2, text="⏸ Pause All", command=self.pause_all_robots)
        pause_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        resume_btn = ttk.Button(btn_frame2, text="▶ Resume All", command=self.resume_all_robots)
        resume_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        remove_btn = ttk.Button(btn_frame2, text="❌ Remove Robot", command=self.remove_robot)
        remove_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Speed control
        speed_frame = ttk.Frame(self.control_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(speed_frame, text="⏱️ Simulation Speed:").pack(side=tk.LEFT)
        self.speed_slider = ttk.Scale(speed_frame, from_=0.1, to=2.0, value=1.0, command=self.update_simulation_speed)
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.speed_value = ttk.Label(speed_frame, text="1.0x")
        self.speed_value.pack(side=tk.LEFT, padx=5)
        
        # Status panel
        self.status_frame = ttk.LabelFrame(right_frame, text="📊 System Status", style='Panel.TLabelframe', padding=10)
        self.status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Current selection info
        self.status_label = ttk.Label(self.status_frame, text="ℹ️ No robot selected", style='Title.TLabel')
        self.status_label.pack(fill=tk.X, pady=(0, 10))
        
        self.robot_count_label = ttk.Label(self.status_frame, text="🤖 Robots: 0")
        self.robot_count_label.pack(fill=tk.X)
        
        # Robot status indicators
        self.status_indicators = ttk.Frame(self.status_frame)
        self.status_indicators.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.status_indicators, text="Status Legend:").pack(side=tk.LEFT)
        ttk.Label(self.status_indicators, text="Moving →", foreground=self.theme['status_legend_moving']).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.status_indicators, text="Waiting ⏳", foreground=self.theme['status_legend_waiting']).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.status_indicators, text="Charging ⚡", foreground=self.theme['status_legend_charging']).pack(side=tk.LEFT, padx=5)
        
        # Information console
        console_frame = ttk.Frame(self.status_frame)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.info_text = scrolledtext.ScrolledText(
            console_frame,
            height=10,
            wrap=tk.WORD,
            state='disabled',
            font=('Consolas', 9),
            background=self.theme['console_bg'],
            foreground=self.theme['console_fg'],
            insertbackground=self.theme['console_fg'],
            selectbackground=self.theme['highlight'],
            selectforeground='white'
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)

    def on_canvas_resize(self, event):
        """Handle canvas resize events to recalculate scaling"""
        self.calculate_scaling_factors()
        self.draw_environment()

    def spawn_robot(self):
        if self.selected_vertex is None:
            messagebox.showwarning("Warning", "Please select a vertex by clicking on it first")
            return
        
        robot = self.fleet_manager.spawn_robot(self.selected_vertex)
        if robot:
            self.robot_colors[robot.id] = robot.color
            self.robot_count_label.config(text=f"🤖 Robots: {len(self.fleet_manager.robots)}")
            self.update_info_text(f"✅ Spawned robot {robot.id} at vertex {self.selected_vertex}")
            self.draw_robots()

    def assign_task(self):
        if self.selected_robot is None:
            messagebox.showwarning("Warning", "Please select a robot by clicking on it first")
            return
        
        if self.selected_vertex is None:
            messagebox.showwarning("Warning", "Please select a destination vertex by clicking on it first")
            return
        
        if self.fleet_manager.assign_task(self.selected_robot, self.selected_vertex):
            self.update_info_text(f"🎯 Assigned task to robot {self.selected_robot}: destination {self.selected_vertex}")
            self.draw_robots()
        else:
            messagebox.showerror("Error", "❌ Could not assign task. Check logs for details.")

    def charge_robot(self):
        if self.selected_robot is None:
            messagebox.showwarning("Warning", "Please select a robot by clicking on it first")
            return
        
        robot = self.fleet_manager.robots[self.selected_robot]
        if robot.status == RobotStatus.CHARGING:
            robot.stop_charging()
            self.status_label.config(text=f"ℹ️ Robot {self.selected_robot} stopped charging")
            self.update_info_text(f"⚡ Robot {self.selected_robot} stopped charging")
        else:
            if self.nav_graph.is_charger(robot.current_vertex):
                robot.charge()
                self.status_label.config(text=f"ℹ️ Robot {self.selected_robot} is charging")
                self.update_info_text(f"⚡ Robot {self.selected_robot} is charging")
            else:
                messagebox.showwarning("Warning", "⚠️ Robot must be at a charging station to charge")
        
        self.draw_robots()

    def pause_all_robots(self):
        for robot in self.fleet_manager.robots.values():
            if robot.status == RobotStatus.MOVING:
                robot.status = RobotStatus.WAITING
        self.update_info_text("⏸ All robots paused")

    def resume_all_robots(self):
        for robot in self.fleet_manager.robots.values():
            if robot.status == RobotStatus.WAITING:
                robot.status = RobotStatus.MOVING
        self.update_info_text("▶ All robots resumed")

    def remove_robot(self):
        if self.selected_robot is None:
            messagebox.showwarning("Warning", "Please select a robot first")
            return
            
        if self.selected_robot in self.fleet_manager.robots:
            del self.fleet_manager.robots[self.selected_robot]
            self.update_info_text(f"❌ Removed robot {self.selected_robot}")
            self.selected_robot = None
            self.robot_count_label.config(text=f"🤖 Robots: {len(self.fleet_manager.robots)}")
            self.draw_robots()

    def update_simulation_speed(self, value):
        speed = float(value)
        for robot in self.fleet_manager.robots.values():
            robot.speed = speed
        self.speed_value.config(text=f"{speed:.1f}x")
        self.update_info_text(f"⏱️ Simulation speed set to {speed:.1f}x")

    def draw_environment(self):
        self.canvas.delete("all")
        
        # Draw a light grid background
        self.draw_grid()
        
        # Draw lanes first
        for lane in self.nav_graph.lanes:
            from_idx, to_idx = lane[0], lane[1]
            start_pos = self._transform_coords(self.nav_graph.get_vertex_position(from_idx))
            end_pos = self._transform_coords(self.nav_graph.get_vertex_position(to_idx))
            
            speed_limit = self.nav_graph.get_lane_speed_limit(from_idx, to_idx)
            lane_color = self.theme['lane'] if speed_limit == 0 else self.theme['lane_speed']
            lane_width = 2 if speed_limit == 0 else 3
            
            # Draw lane with arrow
            self.canvas.create_line(*start_pos, *end_pos, 
                                  fill=lane_color, 
                                  width=lane_width,
                                  arrow=tk.LAST,
                                  arrowshape=(12, 15, 5),
                                  tags="lane")
            
            # Draw speed limit if applicable
            if speed_limit > 0:
                mid_x = (start_pos[0] + end_pos[0]) / 2
                mid_y = (start_pos[1] + end_pos[1]) / 2
                self.canvas.create_text(mid_x, mid_y, 
                                      text=str(speed_limit),
                                      fill='#cc3300',
                                      font=('Arial', 8, 'bold'),
                                      tags="lane_label")

        # Then draw vertices on top
        for i, vertex in enumerate(self.nav_graph.vertices):
            x, y = self._transform_coords(self.nav_graph.get_vertex_position(i))
            name = self.nav_graph.get_vertex_name(i)
            
            # Vertex appearance
            radius = 18 if self.nav_graph.is_charger(i) else 15
            color = self.theme['charger'] if self.nav_graph.is_charger(i) else self.theme['vertex']
            outline = self.theme['charger_outline'] if self.nav_graph.is_charger(i) else self.theme['vertex_outline']
            
            # Draw vertex with shadow effect
            self.canvas.create_oval(
                x-radius+2, y-radius+2, x+radius+2, y+radius+2,
                fill='#aaaaaa', outline='', tags=f"vertex_{i}"
            )
            
            self.canvas.create_oval(
                x-radius, y-radius, x+radius, y+radius,
                fill=color, outline=outline, width=2,
                tags=f"vertex_{i}"
            )
            
            # Vertex label
            label_text = name if name else str(i)
            self.canvas.create_text(
                x, y-radius-20,
                text=label_text,
                font=('Arial', 10, 'bold'),
                fill=self.theme['fg'],
                tags=f"label_{i}"
            )
            
            # Charging station indicator
            if self.nav_graph.is_charger(i):
                self.canvas.create_text(
                    x, y,
                    text="⚡",
                    font=('Arial', 14),
                    fill='#ffffff',
                    tags=f"charger_{i}"
                )

        # Finally draw robots
        self.draw_robots()

    def draw_grid(self):
        """Draw a light grid in the background"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Draw vertical lines
        for x in range(0, width, 50):
            self.canvas.create_line(x, 0, x, height, fill=self.theme['grid'], tags='grid')
        
        # Draw horizontal lines
        for y in range(0, height, 50):
            self.canvas.create_line(0, y, width, y, fill=self.theme['grid'], tags='grid')

    def _transform_coords(self, coords: Tuple[float, float]) -> Tuple[float, float]:
        """Transform real-world coordinates to canvas coordinates"""
        x, y = coords
        # Canvas Y increases downward, so we invert the Y coordinate
        canvas_x = x * self.scale_factor + self.x_offset
        canvas_y = self.canvas.winfo_height() - (y * self.scale_factor + self.y_offset)
        return (canvas_x, canvas_y)

    def draw_robots(self):
        self.canvas.delete("robot")
        
        for robot_id, robot in self.fleet_manager.robots.items():
            pos = robot.get_position()
            if pos:
                x, y = self._transform_coords(pos)
                color = robot.color
                
                # Draw robot with shadow effect
                self.canvas.create_oval(
                    x-12+2, y-12+2, x+12+2, y+12+2,
                    fill='#666666', outline='', tags=("robot", f"robot_{robot_id}")
                )
                
                # Draw main robot body
                self.canvas.create_oval(
                    x-12, y-12, x+12, y+12,
                    fill=color, outline='#333333', width=2,
                    tags=("robot", f"robot_{robot_id}")
                )
                
                # Draw status indicator
                status_symbol, status_color = self.get_status_symbol(robot.status.name)
                self.canvas.create_text(
                    x, y,
                    text=status_symbol,
                    font=('Arial', 12, 'bold'),
                    fill=status_color,
                    tags=("robot", f"robot_{robot_id}")
                )
                
                # Draw robot ID
                self.canvas.create_text(
                    x, y+18,
                    text=f"ID:{robot_id}",
                    font=('Arial', 9),
                    fill=self.theme['fg'],
                    tags=("robot", f"robot_{robot_id}")
                )

    def get_status_symbol(self, status: str) -> Tuple[str, str]:
        symbols = {
            'IDLE': ('I', '#888888'),
            'MOVING': ('→', '#0066ff'),
            'WAITING': ('⏳', '#ff9900'),
            'CHARGING': ('⚡', '#00aa00'),
            'TASK_COMPLETE': ('✓', '#00aa00')
        }
        return symbols.get(status, ('?', '#ff0000'))

    def on_canvas_click(self, event):
        self.canvas.delete("selection")
        
        # First check for robot clicks
        clicked_robot = None
        for robot_id, robot in self.fleet_manager.robots.items():
            pos = robot.get_position()
            if pos:
                x, y = self._transform_coords(pos)
                if math.sqrt((event.x - x)**2 + (event.y - y)**2) <= 15:
                    clicked_robot = robot_id
                    # Highlight selected robot with glow effect
                    for i in range(3, 0, -1):
                        self.canvas.create_oval(
                            x-15-i, y-15-i, x+15+i, y+15+i,
                            outline=self.theme['selection'], width=1,
                            tags="selection"
                        )
                    break
        
        if clicked_robot is not None:
            self.selected_robot = clicked_robot
            robot_status = self.fleet_manager.get_robot_status(clicked_robot)
            self.status_label.config(
                text=f"ℹ️ Selected Robot {clicked_robot} (Status: {robot_status})"
            )
            self.update_info_text(self.status_label.cget("text"))
            return
        
        # If no robot clicked, check for vertex clicks
        clicked_vertex = None
        for i in range(len(self.nav_graph.vertices)):
            x, y = self._transform_coords(self.nav_graph.get_vertex_position(i))
            if math.sqrt((event.x - x)**2 + (event.y - y)**2) <= 20:
                clicked_vertex = i
                # Highlight selected vertex with glow effect
                for i in range(3, 0, -1):
                    self.canvas.create_oval(
                        x-20-i, y-20-i, x+20+i, y+20+i,
                        outline=self.theme['selection'], width=1,
                        tags="selection"
                    )
                break
        
        if clicked_vertex is not None:
            self.selected_vertex = clicked_vertex
            self.selected_robot = None  # Clear robot selection when selecting a vertex
            vertex_name = self.nav_graph.get_vertex_name(clicked_vertex)
            status_text = f"ℹ️ Selected Vertex {clicked_vertex}"
            if vertex_name:
                status_text += f" ({vertex_name})"
            self.status_label.config(text=status_text)
            self.update_info_text(status_text)

    def update_info_text(self, message: str):
        self.info_text.config(state='normal')
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.config(state='disabled')
        
    def draw_blocked_elements(self):
        """Draw visual indicators for blocked lanes and vertices"""
        self.canvas.delete("blocked")
    
        # Draw blocked lanes
        for lane in self.fleet_manager.get_blocked_lanes():
            from_idx, to_idx = lane
            start_pos = self._transform_coords(self.nav_graph.get_vertex_position(from_idx))
            end_pos = self._transform_coords(self.nav_graph.get_vertex_position(to_idx))
        
            self.canvas.create_line(
                *start_pos, *end_pos,
                fill=self.theme['blocked'], width=3, dash=(5,2),
                tags="blocked"
            )
    
        # Draw blocked vertices
        for vertex_id in self.fleet_manager.get_blocked_vertices():
            x, y = self._transform_coords(self.nav_graph.get_vertex_position(vertex_id))
            self.canvas.create_oval(
                x-15, y-15, x+15, y+15,
                outline=self.theme['blocked'], width=3, dash=(5,2),
                tags="blocked"
            )

    def update(self):
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        try:
            # Update robot positions
            self.fleet_manager.update_robots(delta_time)
            
            # Redraw environment
            self.draw_environment()
            self.draw_robots()
            self.draw_blocked_elements()
            
        except Exception as e:
            self.logger.error(f"Error in update loop: {str(e)}")
            self.update_info_text(f"❌ Error: {str(e)}")
        
        # Schedule next update
        self.root.after(50, self.update)