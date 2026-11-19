"""Conservative NERO joint-motion demo in the validated fire-cabinet scene.

Only NERO receives joint-position targets. The cabinet lid remains passive;
this is not a contact-based or active cabinet-opening experiment.
"""
import argparse
import math
from pathlib import Path

from isaaclab.app import AppLauncher

REPO = Path(__file__).resolve().parent.parent
DEFAULT_OVERRIDES = REPO / "assets" / "overrides"

parser = argparse.ArgumentParser(description="NERO joint motion in the fire-cabinet scene")
parser.add_argument("--overrides", default=str(DEFAULT_OVERRIDES))
parser.add_argument("--amplitude", type=float, default=0.18, help="Maximum symmetric offset (rad)")
parser.add_argument("--move-time", type=float, default=2.0, help="Interpolation time per motion (s)")
parser.add_argument("--hold-time", type=float, default=0.6, help="Hold time at each target (s)")
parser.add_argument("--post-demo-time", type=float, default=4.0, help="Final home-pose display time (s)")
parser.add_argument("--cycles", type=int, default=1)
parser.add_argument("--joints", nargs="+", default=["joint1", "joint2", "joint3"])
parser.add_argument("--door-stiffness", type=float, default=2.0)
parser.add_argument("--lid-damping", type=float, default=0.3)
parser.add_argument("--no-extinguisher", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.amplitude <= 0 or args.move_time <= 0 or args.hold_time < 0 or args.post_demo_time < 0:
    parser.error("amplitude/move-time must be positive; hold times cannot be negative")
if args.cycles < 1:
    parser.error("--cycles must be at least 1")
simulation_app = AppLauncher(args).app

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg  # noqa: E402
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg  # noqa: E402
from isaaclab.utils import configclass  # noqa: E402
from isaac_so_arm101.robots.nero_description.nero import NERO_CFG  # noqa: E402

# Same geometry as the accepted passive baseline (2026-11-13).
ROBOT_BASE_POS = (-0.60, 0.0, 0.0)
CAB_POS = (0.40, 0.0, 0.0)
YAW_M90 = (math.sqrt(0.5), 0.0, 0.0, -math.sqrt(0.5))


def validate_assets():
    overrides = Path(args.overrides).expanduser().resolve()
    required = [overrides / "cabinet_articulated.usda"]
    if not args.no_extinguisher:
        required.append(overrides / "extinguisher_rigid.usda")
    asset_root = overrides.parent / "Fire equipment"
    required.append(asset_root / "cabinet" / "cabinet.usdc")
    if not args.no_extinguisher:
        required.append(asset_root / "extinguisher" / "extinguisher.usdc")
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing scene assets:\n  - " + "\n  - ".join(missing)
                                + "\nSee assets/README.md and KANBAN.md Step 7.")


def extinguisher_cfg(name, y):
    return RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/" + name,
        spawn=sim_utils.UsdFileCfg(
            usd_path=str(Path(args.overrides).expanduser().resolve() / "extinguisher_rigid.usda")
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(CAB_POS[0], y, 0.0), rot=YAW_M90
        ),
    )


@configclass
class FireSceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(intensity=2500.0),
    )
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
                stiffness=args.door_stiffness,
                damping=0.3,
                effort_limit_sim=50.0,
            ),
            # Passive lid: zero stiffness, damping only.
            "top_lid_passive": ImplicitActuatorCfg(
                joint_names_expr=["top_lid_joint"],
                stiffness=0.0,
                damping=args.lid_damping,
                effort_limit_sim=50.0,
            ),
        },
    )
    ext_a = extinguisher_cfg("Extinguisher_A", 0.0608)
    ext_b = extinguisher_cfg("Extinguisher_B", -0.0742)


def advance(robot, scene, sim, target, seconds, dt):
    start = robot.data.joint_pos.clone()
    n = max(1, math.ceil(seconds / dt))
    for i in range(1, n + 1):
        if not simulation_app.is_running():
            return False
        robot.set_joint_position_target(start + (target - start) * (i / n))
        scene.write_data_to_sim()
        sim.step()
        scene.update(dt)
    return True


def hold(robot, scene, sim, target, seconds, dt):
    for _ in range(max(0, math.ceil(seconds / dt))):
        if not simulation_app.is_running():
            return False
        robot.set_joint_position_target(target)
        scene.write_data_to_sim()
        sim.step()
        scene.update(dt)
    return True


def safe_amplitude(robot, name, requested, home):
    names = list(robot.joint_names)
    if name not in names:
        raise ValueError(f"Unknown NERO joint '{name}'. Available: {names}")
    jid = names.index(name)
    q0 = float(home[0, jid].item())
    lo, hi = [float(v.item()) for v in robot.data.joint_pos_limits[0, jid]]
    if math.isfinite(lo) and math.isfinite(hi) and hi > lo:
        margin = min(0.05, 0.05 * (hi - lo))
        requested = min(requested, hi - margin - q0, q0 - lo - margin)
    return jid, max(0.0, requested)


def main():
    validate_assets()
    sim = sim_utils.SimulationContext(
        sim_utils.SimulationCfg(dt=0.01, device=args.device)
    )
    sim.set_camera_view([1.2, -0.9, 0.9], [0.0, 0.0, 0.30])
    scene_cfg = FireSceneCfg(num_envs=1, env_spacing=2.0)
    if args.no_extinguisher:
        scene_cfg.ext_a = None
        scene_cfg.ext_b = None
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    robot, cabinet = scene["robot"], scene["cabinet"]
    dt = sim.get_physics_dt()
    home = robot.data.default_joint_pos.clone()
    print("\n[DEMO] NERO joint-motion demo in the fire-cabinet scene.")
    print("[INFO] NERO joints:", robot.joint_names)
    print("[INFO] NERO home positions:", home[0].detach().cpu().tolist())
    print("[INFO] cabinet joints:", cabinet.joint_names)
    print("[INFO] cabinet lid stiffness=0; NO cabinet joint-position targets are sent.")
    print("[INFO] Only NERO.set_joint_position_target() is used; this is not an opening experiment.")

    print("[DEMO] Moving NERO to configured home pose.")
    if not advance(robot, scene, sim, home, 2.0, dt) or not hold(robot, scene, sim, home, 0.5, dt):
        return

    plan = []
    for name in args.joints:
        jid, amp = safe_amplitude(robot, name, args.amplitude, home)
        if amp < 0.02:
            print(f"[WARN] Skip {name}: safe symmetric range is only {amp:.3f} rad.")
        else:
            plan.append((name, jid, amp))
    if not plan:
        raise RuntimeError("No requested joint has enough safe range for the demo.")

    for cycle in range(1, args.cycles + 1):
        print(f"[DEMO] Motion cycle {cycle}/{args.cycles}.")
        for name, jid, amp in plan:
            for sign, label in ((1.0, "+"), (-1.0, "-")):
                target = home.clone()
                target[:, jid] = home[:, jid] + sign * amp
                print(f"[MOVE] {name} {label}{amp:.3f} rad ({math.degrees(amp):.1f} deg).")
                if not advance(robot, scene, sim, target, args.move_time, dt):
                    return
                if not hold(robot, scene, sim, target, args.hold_time, dt):
                    return
            print(f"[MOVE] {name} return to home.")
            if not advance(robot, scene, sim, home, args.move_time, dt):
                return

    print("[DEMO] Returning to home and holding the final pose.")
    if advance(robot, scene, sim, home, args.move_time, dt):
        if hold(robot, scene, sim, home, args.post_demo_time, dt):
            print("[DEMO] Finished successfully.")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
