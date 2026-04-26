class BezierCurve:  # A bezier curve formed by its 4 points.
    def __init__(self, x1=None, y1=None, b2x=None, b2y=None, b3x=None, b3y=None, x2=None, y2=None):
            self.b1x:float = x1
            self.b1y:float = y1
            self.b2x:float = b2x
            self.b2y:float = b2y
            self.b3x:float = b3x
            self.b3y:float = b3y
            self.b4x:float = x2
            self.b4y:float = y2

def SloppySlope(x1, y1, s1, x2, y2, s2) -> BezierCurve: # Requires floats as input
    deltaX = (x2 - x1)

    b2x = x1 + (deltaX / 3)
    b2y = y1 + (s1 * deltaX / 3)

    b3x = x2 - (deltaX / 3)
    b3y = y2 - (s2 * deltaX / 3)

    print(f"[SloppySlope] Bezier 1: {x1}, {y1}")
    print(f"[SloppySlope] Bezier 2: {b2x}, {b2y}")
    print(f"[SloppySlope] Bezier 3: {b3x}, {b3y}")
    print(f"[SloppySlope] Bezier 4: {x2}, {y2}")
    
    return BezierCurve(x1, y1, b2x, b2y, b3x, b3y, x2, y2)

def parse_input_string(input_str):
    """
    Converts a string like '40, 0.6, 0.01' into a float tuple.
    Handles missing values and slope doubling logic.
    """
    try:
        # Clean string and split by commas
        raw_values = [float(x.strip()) for x in input_str.replace('(', '').replace(')', '').split(',')]
        
        frame = raw_values[0]
        val = raw_values[1] if len(raw_values) > 1 else 0.0
        s_last = raw_values[2] if len(raw_values) > 2 else 0.0
        s_first = raw_values[3] if len(raw_values) > 3 else s_last # Double slope logic
        
        return (frame, val, s_last, s_first)
    except Exception as e:
        print(f"Error parsing input: {e}")
        return None

# --- CONSOLE INTERFACE ---
print("==========================================")
print("   HERMITE TO BEZIER CONVERTER")
print("==========================================")
print("Format: Frame, Value, SlopeLast, [SlopeFirst]")
print("Type 'exit' to close.")

while True:
    print("\n--- NEW SEGMENT ---")
    in1 = input("Paste Keyframe 1: ")
    if in1.lower() == 'exit': break
    
    in2 = input("Paste Keyframe 2: ")
    if in2.lower() == 'exit': break
    
    k1 = parse_input_string(in1)
    k2 = parse_input_string(in2)
    
    if k1 and k2:
        # Map parameters to SloppySlope: 
        # s1 is the out-tangent (SlopeFirst) of key 1
        # s2 is the in-tangent (SlopeLast) of key 2
        curve = SloppySlope(k1[0], k1[1], k1[3], k2[0], k2[1], k2[2])
        
        print("\nSUCCESS: Bezier Segment Calculated.")
    else:
        print("Invalid input. Please try again.")

print("Exiting...")