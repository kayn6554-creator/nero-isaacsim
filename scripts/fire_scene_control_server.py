"""Persistent Isaac Sim scene with a localhost TCP control interface for NERO."""
import argparse
import json
import math
import queue
import socket
import threading
from pathlib import Path

from isaaclab.app import AppLauncher

REPO = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description="NERO live control server in the fire-cabinet scene")
parser.add_argument("--overrides", default=str(REPO / "assets" / "overrides"))
parser.add_argument("--control-host", default="127.0.0.1")
parser.add_argument("--control-port", type=int, default=8765)
parser.add_argument("--move-time", type=float, default=2.0)
parser.add_argument("--hold-time", type=float, default=0.4)
parser.add_argument("--door-stiffness", type=float, default=2.0)
parser.add_argument("--lid-damping", type=float, default=0.3)
parser.add_argument("--no-extinguisher", action="store_true")
AppLauncher.add_app_launcher_args(parser)
# CPU PhysX is the validated mode for Shift+left mouse dragging in this scene.
# RTX rendering/WebRTC remains available; only the simulation device is CPU.
parser.set_defaults(device="cpu")
args = parser.parse_args()
if not 1 <= args.control_port <= 65535 or args.move_time <= 0 or args.hold_time < 0:
    parser.error("Invalid control port or motion timing.")

simulation_app = AppLauncher(args).app

# Request PhysX mouse interaction for manual dragging in the streamed viewport.
import carb  # noqa: E402
settings = carb.settings.get_settings()
settings.set_bool("/physics/mouseInteractionEnabled", True)
settings.set_bool("/physics/mouseGrab", True)
settings.set_bool("/physics/forceGrab", True)
print("[INFO] PhysX mouse interaction settings requested.", flush=True)

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg  # noqa: E402
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg  # noqa: E402
from isaaclab.utils import configclass  # noqa: E402
from isaac_so_arm101.robots.nero_description.nero import NERO_CFG  # noqa: E402

ROBOT_BASE_POS = (-0.60, 0.0, 0.0)
CAB_POS = (0.40, 0.0, 0.0)
YAW_M90 = (math.sqrt(0.5), 0.0, 0.0, -math.sqrt(0.5))


def validate_assets():
    overrides = Path(args.overrides).expanduser().resolve()
    required = [overrides / "cabinet_articulated.usda"]
    if not args.no_extinguisher:
        required.append(overrides / "extinguisher_rigid.usda")
    root = overrides.parent / "Fire equipment"
    required.append(root / "cabinet" / "cabinet.usdc")
    if not args.no_extinguisher:
        required.append(root / "extinguisher" / "extinguisher.usdc")
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing scene assets:\n  - " + "\n  - ".join(missing))


def extinguisher_cfg(name, y):
    return RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/" + name,
        spawn=sim_utils.UsdFileCfg(
            usd_path=str(Path(args.overrides).expanduser().resolve() / "extinguisher_rigid.usda")
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(CAB_POS[0], y, 0.0), rot=YAW_M90),
    )


@configclass
class FireSceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(prim_path="/World/ground", spawn=sim_utils.GroundPlaneCfg())
    light = AssetBaseCfg(prim_path="/World/light", spawn=sim_utils.DomeLightCfg(intensity=2500.0))
    robot: ArticulationCfg = NERO_CFG.replace(
        prim_path="{ENV_REGEX_NS}/Robot",
        init_state=NERO_CFG.init_state.replace(pos=ROBOT_BASE_POS),
    )
    cabinet = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cabinet",
        spawn=sim_utils.UsdFileCfg(
            usd_path=str(Path(args.overrides).expanduser().resolve() / "cabinet_articulated.usda"),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                fix_root_link=True, enabled_self_collisions=False
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=CAB_POS, rot=YAW_M90, joint_pos={".*": 0.0}
        ),
        actuators={
            "front_door_hold": ImplicitActuatorCfg(
                joint_names_expr=["front_door_joint"],
                stiffness=args.door_stiffness, damping=0.3, effort_limit_sim=50.0,
            ),
            # Lid is passive: zero stiffness and no scripted joint target.
            "top_lid_passive": ImplicitActuatorCfg(
                joint_names_expr=["top_lid_joint"],
                stiffness=0.0, damping=args.lid_damping, effort_limit_sim=50.0,
            ),
        },
    )
    ext_a = extinguisher_cfg("Extinguisher_A", 0.0608)
    ext_b = extinguisher_cfg("Extinguisher_B", -0.0742)


def make_target(robot, home, changes):
    target = home.clone()
    names = list(robot.joint_names)
    for name, delta in changes.items():
        if name not in names:
            raise ValueError(f"Joint {name!r} not found; joints={names}")
        jid = names.index(name)
        q0 = float(home[0, jid].item())
        lo, hi = [float(x.item()) for x in robot.data.joint_pos_limits[0, jid]]
        value = q0 + delta
        if math.isfinite(lo):
            value = max(value, lo + 0.04)
        if math.isfinite(hi):
            value = min(value, hi - 0.04)
        target[0, jid] = value
    return target


def build_segments(command, robot, home):
    duration, hold = args.move_time, args.hold_time
    neutral = home.clone()
    # Conservative coordinated shoulder/elbow pose; confirm visual direction at first run.
    forward = make_target(robot, home, {"joint2": 0.12, "joint3": -0.12})
    left = make_target(robot, home, {"joint1": 0.12})
    right = make_target(robot, home, {"joint1": -0.12})
    if command in ("home", "back", "retract"):
        poses = [("return home", neutral)]
    elif command in ("forward", "reach"):
        poses = [("small reach pose", forward)]
    elif command in ("sway", "wave"):
        poses = [("yaw left", left), ("yaw right", right), ("return home", neutral)]
    elif command == "demo":
        poses = [("forward/reach", forward), ("back/home", neutral),
                 ("yaw left", left), ("yaw right", right), ("return home", neutral)]
    else:
        raise ValueError(f"Unknown command: {command}")
    return [(label, pose, duration, hold) for label, pose in poses]


def main():
    validate_assets()
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=0.01, device=args.device))
    print(f"[INFO] Simulation/PhysX device: {args.device}", flush=True)
    sim.set_camera_view([1.2, -0.9, 0.9], [-0.1, 0.0, 0.30])
    cfg = FireSceneCfg(num_envs=1, env_spacing=2.0)
    if args.no_extinguisher:
        cfg.ext_a = None
        cfg.ext_b = None
    scene = InteractiveScene(cfg)
    sim.reset()
    robot, cabinet = scene["robot"], scene["cabinet"]
    dt = sim.get_physics_dt()
    home = robot.data.default_joint_pos.clone()
    idle_target = home.clone()

    requests = queue.Queue()
    stop_server = threading.Event()
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((args.control_host, args.control_port))
    listener.listen(4)
    listener.settimeout(0.5)
    state = {"motion": None, "running": True}

    def serve_client(conn):
        with conn:
            stream = conn.makefile("rwb")
            for raw in stream:
                try:
                    data = json.loads(raw.decode("utf-8"))
                    command = str(data.get("command", "")).strip().lower()
                    if not command:
                        raise ValueError("Request requires a command field.")
                    req = {"command": command, "event": threading.Event()}
                    requests.put(req)
                    if not req["event"].wait(10.0):
                        response = {"ok": False, "message": "Simulation did not acknowledge within 10 seconds."}
                    else:
                        response = req["response"]
                except Exception as exc:
                    response = {"ok": False, "message": str(exc)}
                try:
                    stream.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
                    stream.flush()
                except OSError:
                    return

    def accept_loop():
        while not stop_server.is_set():
            try:
                conn, _ = listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=serve_client, args=(conn,), daemon=True).start()

    threading.Thread(target=accept_loop, name="nero-control-tcp", daemon=True).start()

    def reply(req, ok, message, **fields):
        req["response"] = {"ok": ok, "message": message, **fields}
        req["event"].set()

    def handle_requests():
        nonlocal idle_target
        while True:
            try:
                req = requests.get_nowait()
            except queue.Empty:
                return
            command = req["command"]
            if command in ("help", "?"):
                reply(req, True, "Commands: demo, forward, back, sway, home, stop, status, quit.")
            elif command == "status":
                reply(req, True, "Status.", active=state["motion"] is not None,
                      joint_positions=robot.data.joint_pos[0].detach().cpu().tolist())
            elif command == "stop":
                state["motion"] = None
                idle_target = robot.data.joint_pos.clone()
                reply(req, True, "Stopped; holding current NERO pose.")
                print("[CONTROL] STOP: holding current pose.", flush=True)
            elif command == "quit":
                state["running"] = False
                reply(req, True, "Stopping simulation server.")
            elif state["motion"] is not None:
                reply(req, False, "NERO is moving. Wait, or send stop first.")
            else:
                try:
                    segments = build_segments(command, robot, home)
                    state["motion"] = {
                        "segments": segments, "index": 0, "phase": "move",
                        "elapsed": 0.0, "start": robot.data.joint_pos.clone(),
                    }
                    reply(req, True, f"Accepted command: {command}.")
                    print(f"[CONTROL] Accepted command: {command}", flush=True)
                except Exception as exc:
                    reply(req, False, str(exc))

    def update_motion():
        nonlocal idle_target
        motion = state["motion"]
        if motion is None:
            robot.set_joint_position_target(idle_target)
            return
        label, target, duration, hold = motion["segments"][motion["index"]]
        motion["elapsed"] += dt
        if motion["phase"] == "move":
            alpha = min(1.0, motion["elapsed"] / duration)
            robot.set_joint_position_target(motion["start"] + (target - motion["start"]) * alpha)
            if alpha >= 1.0:
                motion["phase"] = "hold"
                motion["elapsed"] = 0.0
                print(f"[MOVE] {label} reached.", flush=True)
        else:
            robot.set_joint_position_target(target)
            if motion["elapsed"] >= hold:
                motion["index"] += 1
                if motion["index"] >= len(motion["segments"]):
                    idle_target = target.clone()
                    state["motion"] = None
                    print("[CONTROL] Motion finished; holding final pose.", flush=True)
                else:
                    motion["start"] = target.clone()
                    motion["phase"] = "move"
                    motion["elapsed"] = 0.0

    print("\n[SCENE] NERO + fire cabinet scene ready.", flush=True)
    print("[INFO] NERO joints:", robot.joint_names, flush=True)
    print("[INFO] Cabinet joints:", cabinet.joint_names, flush=True)
    print("[INFO] Lid stiffness=0; no cabinet joint-position targets are sent.", flush=True)
    print("[INFO] Gravity/collisions remain enabled; mouse interaction requested.", flush=True)
    print(f"[CONTROL] Listening on {args.control_host}:{args.control_port}", flush=True)
    print("[CONTROL] Second terminal: .venv/bin/python scripts/nero_motion_client.py demo", flush=True)
    print("[WEBRTC] Connect to 192.168.1.102.", flush=True)

    try:
        while simulation_app.is_running() and state["running"]:
            handle_requests()
            update_motion()
            scene.write_data_to_sim()
            sim.step()
            scene.update(dt)
    finally:
        stop_server.set()
        listener.close()
        simulation_app.close()


if __name__ == "__main__":
    main()
