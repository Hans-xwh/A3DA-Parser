import json
import struct

### Config ###
json_path = r"C:\something"
dsc_path = r"C:\something"
target_game = "info_FT"
##############


def read_OpCodes(json_path:str, target_game:str) -> dict[int, tuple]:
    mappings:dict[int, tuple] = {}

    print(f"[read_OpCodes] Looking opcodes for: {target_game}")
    with open(json_path, "r") as db:
        json_data = json.load(db)
        for name, contents in json_data.items():
            for version, data in contents.items():
                if version == target_game:
                    opcode = int(data["id"])
                    mappings[opcode] = (
                        data["len"],
                        name
                    )
                    #print(opcode, mappings[opcode])
    

    return dict(sorted(mappings.items()))


def read_dsc(dsc_path:str, opcodes:dict[int, tuple]):
    with open(dsc_path, "rb") as f:
        header = f.read(12)     #Header is always 12 bytes i think, at least for FT

        print("--- Reading DSC ---")
        while True:     #Main loop to read dsc
            #Read opcode
            data = f.read(4)

            if not data:    #Break on end of file
                break

            opcode = struct.unpack('<i', data)[0]
            length, name = opcodes.get(opcode)

            #Read params
            params = []
            if length > 0:
                data = f.read(4*length)
                params = struct.unpack(f'{length}i', data)

            #Print command
            param_string = ""
            for param in params:
                param_string += str(param)
                if param != params[-1]:
                    param_string += ", "
            print(f'{name}({param_string});')
    pass


print("--- Start ---")

mappings = read_OpCodes(json_path, target_game)
print(mappings)
read_dsc(dsc_path, mappings)
