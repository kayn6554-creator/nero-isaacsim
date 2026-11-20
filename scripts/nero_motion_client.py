"""Send a single command to the running NERO Isaac Sim control server."""
import argparse
import json
import socket

parser = argparse.ArgumentParser(description="Send a NERO motion command to the running Isaac Sim.")
parser.add_argument("command", nargs="?", default="help",
                    choices=["demo", "forward", "reach", "back", "retract", "sway", "wave", "home", "stop", "status", "help", "quit"])
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=8765)
parser.add_argument("--timeout", type=float, default=12.0)
args = parser.parse_args()

payload = (json.dumps({"command": args.command}) + "\n").encode("utf-8")
with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
    sock.sendall(payload)
    stream = sock.makefile("rb")
    line = stream.readline()
    if not line:
        raise SystemExit("Control server closed without a response.")
    response = json.loads(line.decode("utf-8"))
    print(response.get("message", response))
    if response.get("joint_positions") is not None:
        print("Joint positions:", response["joint_positions"])
    if not response.get("ok", False):
        raise SystemExit(1)
