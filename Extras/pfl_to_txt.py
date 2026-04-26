from pathlib import Path

### Config ###
in_pfl = Path("")
out_file = Path()


def read_pfl(in_path:Path) -> list[str] | None:
    print("\nReading...")
    with in_path.open("rb") as pfl:
        strings = []

        header = pfl.read(64)   #Im ASSUMING the header is always 64 bytes

        ## Divafile handling ##
        if header[:8] == b'\x44\x49\x56\x41\x46\x49\x4C\x45':
            print("ERROR: Encrypted DIVAFILE couldn't be read")
            return None
        
        while True:
            chunk = pfl.readline()
            if not chunk: break

            chunk = chunk.split(b'\x00')[0].decode("utf-8")
            strings.append(chunk)
            #print(chunk.strip())

        return strings


def save_pvField(out_path:Path, strings:list[str]):
    print("\nSaving file...")

    with out_path.open(mode="w") as pv_field:
        if not pv_field.writable:
            print("Unable to write to selected path!!!")
            return

        for s in strings:
            pv_field.write(s)
    
    print(f'pv_field saved successfully to: {out_path}')


def main(in_pfl:Path, out_file:Path):
    print("\n==== PFL -> TXT ===")

    if not in_pfl.is_file():
        path = input("Insert input .pfl path: ")
        in_pfl = Path(path.strip('"'))

    lines = read_pfl(in_pfl)

    if lines:
        if not out_file.is_file():
            print("Writing to current directory")
            #out_file = Path.cwd() / in_pfl.with_suffix(".txt")
            out_file = Path.cwd() / f'{in_pfl.stem}.txt'

        save_pvField(out_file, lines)


if __name__ == "__main__":
    main(in_pfl, out_file)