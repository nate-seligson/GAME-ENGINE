import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from render import Renderer
class RotationVisualizer:
    def __init__(self):
        self.renderer = Renderer(rpm=20)
        self.period = 1.5  # Half-rotation period in seconds (20 RPM)
        self.max_radius = 64
        
        # Extract and sort activation events
        self.activation_events = []
        for timing_ms, data_list in self.renderer.renderDict.items():
            timing_sec = timing_ms / 1000.0
            for data in data_list:
                self.activation_events.append((timing_sec, data['x'], data['y']))
        
        self.activation_events.sort(key=lambda x: x[0])
        self.event_index = 0
        
        # Setup plot
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.ax.set_xlim(-self.max_radius-5, self.max_radius+5)
        self.ax.set_ylim(-self.max_radius-5, self.max_radius+5)
        self.ax.set_aspect('equal')
        self.ax.set_title("Half-Rotation POV Display")
        
        # Visualization elements
        self.scat = self.ax.scatter([], [], s=3, c='blue')
        self.ref_line, = self.ax.plot([], [], c='red', alpha=0.5)
        self.active_leds = np.zeros((0, 2))
        self.rotation_phase = 0  # 0 = forward, 1 = backward

    def calculate_line_pos(self, t):
        """Calculate current line position based on time"""
        angle = (t / self.period) * math.pi
        return np.array([
            self.max_radius * math.cos(angle),
            self.max_radius * math.sin(angle)
        ])

    def update(self, frame):
        current_time = (frame / 30) % (2 * self.period)  # Full cycle period
        
        # Handle both forward and backward phases
        if current_time < self.period:
            self.rotation_phase = 0
            phase_time = current_time
        else:
            self.rotation_phase = 1
            phase_time = current_time - self.period

        # Add new LEDs that should have been activated
        while self.event_index < len(self.activation_events):
            t, x, y = self.activation_events[self.event_index]
            
            # Adjust timing for backward phase
            if self.rotation_phase == 1:
                t = self.period - t
                
            if t <= phase_time:
                self.active_leds = np.vstack([self.active_leds, [x, y]])
                self.event_index += 1
            else:
                break

        # Update line position
        line_end = self.calculate_line_pos(phase_time)
        if self.rotation_phase == 1:
            line_end *= -1  # Reverse direction for backward phase
            
        self.ref_line.set_data([0, line_end[0]], [0, line_end[1]])
        self.scat.set_offsets(self.active_leds)

        # Reset at end of cycle
        if frame % (60 * 30) == 0:  # Reset every 60 frames for demo
            self.active_leds = np.zeros((0, 2))
            self.event_index = 0

        return self.scat, self.ref_line

    def animate(self):
        ani = animation.FuncAnimation(
            self.fig, self.update,
            frames=int(2 * self.period * 30),  # 30 FPS for forward+backward
            interval=33,  # ~30 FPS
            blit=True
        )
        plt.show()

# Run the visualization
visualizer = RotationVisualizer()
visualizer.animate()