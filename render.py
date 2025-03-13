import math
import socket
import time
import struct

pixel_count = 24
pixel_distance = 1

class Renderer:
    def __init__(self, pixel_count=pixel_count, pixel_distance=pixel_distance, rpm=3000, LEDs_x=64, LEDs_y=32):
        # rotation per minute and per second
        self.rpm = rpm / 2
        self.rps = self.rpm / 60
        self.sock = None
        # convert grid of pixels to a render queue -- after some seconds to wait, display this screen 
        print("Building render dictionary...")
        self.renderDict = {}

        for a in range(-pixel_count, pixel_count, pixel_distance):
            for b in range(-pixel_count, pixel_count, pixel_distance):
                bottom = b < 0 if b != 0 else a < 0
                a_squared = (a ** 2)
                b_squared = (b ** 2)
                # constrain pixel_x to grid limits
                pixel_x = min(max(round(math.sqrt(a_squared + b_squared)), 0), LEDs_x)
                
                # calculate angle at which pixel should be displayed
                angle = math.atan2(b, a)
                if angle <= 0:
                    angle += (2 * math.pi)

                if bottom:
                    angle -= math.pi
                    pixel_x *= -1
                # calculate timing (ms) for this pixel
                time_for_one_rotation = (1 / self.rps * 1000)  # for half the screen
                ratio = angle / (2 * math.pi)
                timing_final_ms = int(time_for_one_rotation * ratio)

                if angle > math.pi:
                    pixel_x *= -1
                    timing_final_ms -= (time_for_one_rotation / 2)
                # add to render dict
                position_x = (a + pixel_count)
                position_y = (b + pixel_count)
                data = {"activePixel": pixel_x, "x": position_x, "y": position_y}
                if timing_final_ms in self.renderDict:
                    self.renderDict[timing_final_ms].append(data)
                else:
                    self.renderDict[timing_final_ms] = [data]

    def createPipeline(self, graphicsSlice, y):
        pipeline = {}
        for delay, values in self.renderDict.items():
            for data in values:
                x, z = (data['x'], data['y'])
                if (x, z) in graphicsSlice.keys():
                    color = graphicsSlice[(x, z)]
                    if delay not in pipeline.keys():
                        pipeline[delay] = [((data["activePixel"], y), color)]
                    else:
                        pipeline[delay] += [((data["activePixel"], y), color)]
        return pipeline

    def convertToTiming(self, scene):
        # create "master pipeline" from all XZ planes and combine them
        master_pipeline = {}
        for y in range(len(scene[0])):
            graphicsSlice = {}
            for x in range(len(scene)):
                for z in range(len(scene[x][y])):
                    if scene[x][y][z] is not None:
                        graphicsSlice[(x, z)] = scene[x][y][z]
            if y == 0:
                master_pipeline = self.createPipeline(graphicsSlice, y)
            else:
                for key, value in self.createPipeline(graphicsSlice, y).items():
                    if key not in master_pipeline.keys():
                        master_pipeline[key] = value
                    else:
                        master_pipeline[key] += value
        # sort master pipeline & simplify delays so one comes after the other
        ordered_keys = sorted(master_pipeline.keys())
        subtractor = 0
        timings = []
        positions = []
        for key in ordered_keys:
            timings.append(key - subtractor)
            positions.append(master_pipeline[key])
            subtractor = key
        return positions, timings

    def sendToDevice(self, scene, host='192.168.1.186', port=8888):
        positions, timings = self.convertToTiming(scene)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                self.sock = sock
                # Enable TCP_NODELAY to bypass Nagle’s algorithm (minimizes delays)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.sock.settimeout(2)  # Default timeout for general operations
                self.sock.connect((host, port))
                print(f"Connected to {host}:{port}")

                # Send initialization ping immediately (no sleep)
                self.sock.sendall(b"loop\n")
                while True:
                    self.send_positions_over_wifi(positions,timings)
        except (ConnectionRefusedError, socket.timeout) as e:
            print(f"Network error: {str(e)}")
        except Exception as e:  
            print(f"Unexpected error: {str(e)}")

    def process_frames(self, positions, timings):
        sock = self.sock
        """
        Process and send frames over the socket. If a reset signal (0 byte) is received,
        exit early from all loops.
        
        Returns True if a reset signal was detected; False otherwise.
        """
        # Precompile struct for rapid pixel packing (5 bytes per pixel)
        pixel_fmt = struct.Struct('BBBBB')
        for i in [1, -1]:
            for frame, timing in zip(positions, timings):
                # Save the current timeout and set a short one to check for reset signal.
                original_timeout = sock.gettimeout()
                try:
                    sock.settimeout(0.00001)
                    data = sock.recv(1)
                    if data and data == b'\x00':  # Reset signal detected
                        return True
                except socket.timeout:
                    # No reset signal, continue processing
                    pass
                finally:
                    sock.settimeout(original_timeout)
                
                # Clamp timing between 0 and 1500
                frame_delay = max(0, min(int(timing), 1500))
                buffer = bytearray()
                
                # Process each pixel in the frame
                for (x, y), (r, g, b) in frame:
                    # Transform coordinates – if static, consider precomputing these.
                    panel_x = max(0, min((x * i) + 31, 63))
                    panel_y = max(0, min(y, 31))
                    buffer.extend(pixel_fmt.pack(panel_x, panel_y, r, g, b))
                
                # Append frame metadata: 2 bytes delay + 2-byte end marker
                buffer.extend(frame_delay.to_bytes(2, 'big'))
                buffer.extend(b'\xFF\xFF')
                
                # Send the entire frame immediately
                sock.sendall(buffer)
        return False

    def send_positions_over_wifi(self, positions, timings):
        sock = self.sock
        reset_detected = self.process_frames(sock, positions, timings)
        # Optionally, you can adjust this timeout as needed.
        while not reset_detected:
            sock.settimeout(1)
            try:
                data = sock.recv(1)
                if data and data == b'\x00':
                    break  # Restart frame processing
            except socket.timeout:
                # No reset received within timeout; assume continuation of operation.
                print("No reset signal received")

if __name__ == "__main__":
    # Example usage with WiFi parameters
    r = Renderer(rpm=1000)
    
    scene = [[[(255, 0, 255) if z < 32 else (255,0,0) for z in range(pixel_count * 2)] for _ in range(32)] for _ in range(pixel_count * 2)]
    
    # Send to device (replace IP with your ESP32's IP)
    r.sendToDevice(scene)   