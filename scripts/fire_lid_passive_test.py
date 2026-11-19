"""Passive fire-cabinet lid baseline test: NERO + cabinet + two extinguishers.

The top lid is NOT position-commanded. Its actuator stiffness is zero; only
configurable joint damping remains. The front door is held at its default
closed position by a weak spring actuator.

This is a simulation-only passive baseline, not an active lid-opening policy.
"""

import argparse
import os

from isaaclab.app import AppLauncher

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parser = argparse.ArgumentParser(description="Passive fire-cabinet lid baseline test.")
parser.add_argument("--overrides", default=os.path.join(REPO, "assets", "overrides"))
parser.add_argument("--door_stiffness", type=float, default=2.0)
parser.add_argument("--lid_damping", type=float, default=0.3)
parser.add_argument("--no_extinguisher", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
simulation_app = AppLauncher(args).app

import math  # noqa: E402

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg  # noqa: E402
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg  # noqa: E402
from isaaclab.utils import configclass  # noqa: E402

from isaac_so_arm101.robots.nero_description.nero import NERO_CFG  # noqa: E402

# Baseline-only offset: keep the default NERO pose clear of the cabinet.
# Do not modify the shared NERO_CFG in nero.py.
ROBOT_BASE_POS = (-0.60, 0.0, 0.0)

CAB_POS = (0.40, 0.0, 0.0)
YAW_M90 = (math.sqrt(0.5), 0.0, 0.0, -math.sqrt(0.5))
EXT_A_POS = (CAB_POS[0], 0.0608, 0.0)
EXT_B_POS = (CAB_POS[0], -0.0742, 0.0)


def ext_cfg(name: str, pos) -> RigidObjectCfg:
    return RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/" + name,
        spawn=sim_utils.UsdFileCfg(usd_path=f"{args.overrides}/extinguisher_rigid.usda"),
        init_state=RigidObjectCfg.InitialStateCfg(pos=pos, rot=YAW_M90),
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
            usd_path=f"{args.overrides}/cabinet_articulated.usda",
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                fix_root_link=True,
                enabled_self_collisions=False,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=CAB_POS,
            rot=YAW_M90,
            joint_pos={".*": 0.0},
        ),
        actuators={
            "front_door_hold": ImplicitActuatorCfg(
                joint_names_expr=["front_door_joint"],
                stiffness=args.door_stiffness,
                damping=0.3,
                effort_limit_sim=50.0,
            ),
            # Passive lid: no position-restoring stiffness, damping only.
            "top_lid_passive": ImplicitActuatorCfg(
                joint_names_expr=["top_lid_joint"],
                stiffness=0.0,
                damping=args.lid_damping,
                effort_limit_sim=50.0,
            ),
        },
    )

    ext_a = ext_cfg("Extinguisher_A", EXT_A_POS)
    ext_b = ext_cfg("Extinguisher_B", EXT_B_POS)


def main():
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=0.01, device=args.device))
    sim.set_camera_view([1.2, -0.9, 0.9], [0.35, 0.0, 0.3])

    scene_cfg = FireSceneCfg(num_envs=1, env_spacing=2.0)
    if args.no_extinguisher:
        scene_cfg.ext_a = None
        scene_cfg.ext_b = None

    scene = InteractiveScene(scene_cfg)
    sim.reset()

    robot = scene["robot"]
    cab = scene["cabinet"]
    lid_id = cab.find_joints("top_lid_joint")[0][0]
    door_id = cab.find_joints("front_door_joint")[0][0]
    exts = [scene[k] for k in ("ext_a", "ext_b") if not args.no_extinguisher]

    print("\n[BASELINE] Passive top-lid test started.")
    print("[INFO] robot root position:", robot.data.root_pos_w[0].detach().cpu().tolist())
    print("[INFO] cabinet root position:", cab.data.root_pos_w[0].detach().cpu().tolist())
    print("[INFO] robot joints:", robot.joint_names)
    print("[INFO] cabinet joints:", cab.joint_names)
    print("[INFO] cabinet bodies:", cab.body_names)
    print("[INFO] cabinet joint limits (rad):", cab.data.joint_pos_limits[0].tolist())
    print("[INFO] cabinet DOF stiffness:", cab.root_physx_view.get_dof_stiffnesses()[0].tolist())
    print("[INFO] lid damping:", args.lid_damping)
    print("[INFO] door hold stiffness:", args.door_stiffness)
    print("[INFO] No cabinet.set_joint_position_target() calls are used in this script.")

    dt = sim.get_physics_dt()
    step = 0
    while simulation_app.is_running():
        # Hold only NERO at home. The cabinet receives no joint-position targets.
        robot.set_joint_position_target(robot.data.default_joint_pos)
        scene.write_data_to_sim()
        sim.step()
        scene.update(dt)
        step += 1

        if step % 50 == 0:
            q = cab.data.joint_pos[0]
            qd = cab.data.joint_vel[0]
            tau = cab.data.applied_torque[0]
            msg = (
                f"t={step * dt:7.2f}s  "
                f"lid={math.degrees(q[lid_id].item()):8.2f}deg "
                f"lid_vel={math.degrees(qd[lid_id].item()):8.2f}deg/s "
                f"lid_tau={tau[lid_id].item():7.3f}Nm  "
                f"door={math.degrees(q[door_id].item()):8.2f}deg "
                f"door_vel={math.degrees(qd[door_id].item()):8.2f}deg/s"
            )
            for i, extinguisher in enumerate(exts):
                p = extinguisher.data.root_pos_w[0] - scene.env_origins[0]
                msg += f"  ext{i}=({p[0].item():.3f},{p[1].item():.3f},{p[2].item():.3f})"
            print(msg)


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
