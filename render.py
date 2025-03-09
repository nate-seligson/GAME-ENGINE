import math
class Renderer:
    def __init__(self, pixel_count = 45, pixel_distance = 5, rpm = 3000, LEDs_x = 64, LEDs_y = 32):
        #rotation per min and rotation per second
        self.rpm = rpm
        self.rps = rpm/60

        #convert grid of pixels to a render queue -- after some seconds to wait, display this screen 
        print("building render dictionary...")
        self.renderDict = {}
        self.renderQueue = []
        self.testQueue = []
        for a in range(-pixel_count, pixel_count, pixel_distance):
            for b in range(-pixel_count, pixel_count, pixel_distance):
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
                #calculate timing required to meet angle (ratio of 2pi : time_for_one_rotation)
                time_for_one_rotation = 1/self.rps * 1000
                self.testQueue.append((pixel_x * math.cos(angle), pixel_x * math.sin(angle)))
                ratio = angle/(2*math.pi)
                timing_final_ms = int(time_for_one_rotation * ratio)
                ##add to render dict
                #create pixel array if such does not exist 
                data = {"activePixel":pixel_x, "x":a, "y":b}
                if timing_final_ms in self.renderDict:
                    self.renderDict[timing_final_ms].append(data)
                else:
                    self.renderDict[timing_final_ms] = [data]

        #TO ADD make it so that it only goes for half and splits the screen in two
        sorted_keys = list(self.renderDict.keys())
        # Sort the keys
        sorted_keys.sort()
        
        #make renderer queue
        for key in sorted_keys:
            #make time waits accurate to the steps after the last wait
            key_index = sorted_keys.index(key)
            #first index has no adjustment
            if key_index == 0:
                adjusted_key = key
            else:
                adjusted_key = key - sorted_keys[key_index-1]
            self.renderQueue.append((adjusted_key, self.renderDict[key]))
        print(self.renderQueue)

                
    def convertToTiming(scene):
        print("converting...")
    def sendToDevice():
        print("sent to device")
Renderer(rpm = 20)