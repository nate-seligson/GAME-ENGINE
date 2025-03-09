import math
from scene import Scene
import json
pixel_count = 24
pixel_distance = 1
class Renderer:
    def __init__(self, pixel_count = pixel_count, pixel_distance = pixel_distance, rpm = 3000, LEDs_x = 64, LEDs_y = 32):
        #rotation per min and rotation per second
        self.rpm = rpm
        self.rps = rpm/60

        #convert grid of pixels to a render queue -- after some seconds to wait, display this screen 
        print("building render dictionary...")
        self.renderDict = {}
        self.testQueue = []

        for a in range(-pixel_count, pixel_count, pixel_distance):
            for b in range(-pixel_count, pixel_count, pixel_distance):
                bottom = b < 0 if b!= 0 else a<0
                #get closest x pixel to grid point
                a_squared = (a ** 2)
                b_squared = (b ** 2)
                #max in min to hold back overflow
                pixel_x = min(max(round(math.sqrt(a_squared + b_squared)), 0),LEDs_x)
                
                ##calculate angle at which pixel should be displayed

                angle = math.atan2(b,a)
                #make it clamped between 0 to 2pi instead od -pi to pi
                if angle <= 0:
                    angle += (2 * math.pi)

                if bottom:
                    angle -= math.pi
                    pixel_x *= -1
                #calculate timing required to meet angle (ratio of 2pi : time_for_one_rotation)
                time_for_one_rotation = (1/self.rps * 1000) # for half the screen
                self.testQueue.append((pixel_x * math.cos(angle), pixel_x * math.sin(angle)))
                ratio = angle/(2 * math.pi)
                timing_final_ms = int(time_for_one_rotation * ratio)

                if angle > math.pi:
                    pixel_x *= -1
                    timing_final_ms -= (time_for_one_rotation / 2)
                ##add to render dict
                #create pixel array if such does not exist
                position_x = (a + pixel_count)
                position_y = (b + pixel_count)

                data = {"activePixel":pixel_x, "x":position_x, "y":position_y}
                if timing_final_ms in self.renderDict:
                    self.renderDict[timing_final_ms].append(data)
                else:
                    self.renderDict[timing_final_ms] = [data]
    def createPipeline(self, graphicsSlice, y):
        pipeline = {}
        for delay,values in self.renderDict.items():
            for data in values:
                x,z = (data['x'],data['y'])
                if (x,z) in graphicsSlice.keys():
                    color = graphicsSlice[(x,z)]
                    pipeline[delay] = [((data["activePixel"], y), color)]
        return pipeline

    def convertToTiming(self,scene):
        #create "master pipeline" from all XZ planes and combining them
        master_pipeline = {}
        for y in range(len(scene.graphics[0])):
            graphicsSlice = {}
            for x in range(len(scene.graphics)):
                for z in range(len(scene.graphics[x][y])):
                    if scene.graphics[x][y][z] != None:
                        graphicsSlice[(x,z)] = scene.graphics[x][y][z]
            #init master pipeline
            if y == 0:
                master_pipeline = self.createPipeline(graphicsSlice, y)
            else:
                #add to master pipeline if already existant
                for key,value in self.createPipeline(graphicsSlice, y).items():
                    if key not in master_pipeline.keys():
                        master_pipeline[key] = value
                    else:
                        master_pipeline[key] += value
        
        #sort master pipeline -- simplify delays so one comes after the other
        ordered_keys = sorted(master_pipeline.keys())
        subtractor = 0
        sorted_master_pipeline = {}
        for key in ordered_keys:
            sorted_master_pipeline[key - subtractor] = master_pipeline[key]
            subtractor = key
        return sorted_master_pipeline
        
                    

    def sendToDevice():
        print("sent to device")
g = Scene()
g.graphics = [[[0 for i in range(pixel_count * 2)] for j in range(10)] for p in range(pixel_count * 2)]
with open("forge.json", "r") as file:
    g.graphics = json.load(file)["data"]
    x = Renderer(rpm = 20).convertToTiming(g)
    print(x)