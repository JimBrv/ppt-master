import sys
import pathlib
import argparse

def main():
    parser = argparse.ArgumentParser(description="Safely write file contents via STDIN (PTY Buffer Bypass).")
    parser.add_argument("target_path", help="The path of the file to write.")
    parser.add_argument("--eof", default="<<EOF>>", help="The EOF delimiter for manual terminal input mode.")
    args = parser.parse_args()

    out_path = pathlib.Path(args.target_path)
    # Ensure parents exist
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[file_write] Target: {out_path}. Consuming STDIN...")
    lines = []
    
    # Read until EOF (for redirects) or delimiter (for manual/PTY piping)
    for line in sys.stdin:
        if line.strip() == args.eof:
            break
        lines.append(line)
        
    content = "".join(lines)
    out_path.write_text(content, encoding="utf-8")
    print(f"[file_write] Successfully wrote {len(content)} bytes to {out_path.name}")

if __name__ == "__main__":
    main()
