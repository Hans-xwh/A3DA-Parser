

framerate = 60

def DscToFrame(dsc) -> int:  #Convert Diva Script time to Blender frames, in ints
    frames = dsc/100000
    frames = round(frames * framerate)       #Not entirely sure this is correct
    #frames = math.celi(frames/60)
    return frames

def FrameToDsc(frame) -> int:  #Convert Blender frames to Diva Script time, in ints
    dsc = frame / framerate
    dsc = round(dsc * 100000)
    return dsc

def UI():
    print(f"Diva Script Time <-> Blender Frames Converter. Using {framerate} FPS.")
    while True:
        print("DSC time (d) <-> Frames (f)")
        inpt = input(": ")  #User will input d or f followed by a space and the value. Default is d to f.

        #In case user is sloppy (I am, thats why i do this lol)
        if not inpt.startswith("d") and not inpt.startswith("D") and not inpt.startswith("f") and not inpt.startswith("F"):
            inpt = f"d{inpt}"

        #Define conversion direction
        if inpt.startswith("d") or inpt.startswith("D"):
            try:
                value = float(inpt.strip("dD "))
                result = DscToFrame(value)
                print(f"{value} DSC -> {result} frames.")
            except ValueError:
                print("Invalid input")#. Please enter a valid integer after 'd '.")
        elif inpt.startswith("f") or inpt.startswith("F"):
            try:
                value = float(inpt.strip("fF "))
                result = FrameToDsc(value)
                print(f"{value} frames -> {result} DSC.")
            except ValueError:
                print("Invalid input")#. Please enter a valid integer after 'f '.")

        print("\n")
        

if __name__ == "__main__":
    UI()