"""消防箱资产测试：NERO + 消防箱（关节体）+ 两个灭火器。

这一版机械臂不动，只用脚本强制开/关顶盖和前门，检查：
  1. 资产能不能作为 IsaacLab 关节体加载（关节名、限位、转轴方向）
  2. 松开后门在重力下的表现（顶盖应保持关闭，前门由一个弱“门扣”弹簧拉住）
  3. 灭火器有没有穿模、掉落

运行（在 /data/panhe/isaac_nero 下）：
  .venv/bin/python scripts/fire_cabinet_test.py --headless --livestream 2

资产覆盖层在 assets/overrides/ 下，它们按相对路径引用 assets/Fire equipment/ 里的原始资产。
"""

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Fire cabinet asset test with NERO.")
import os  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parser.add_argument("--overrides", default=os.path.join(REPO, "assets", "overrides"),
                    help="cabinet_articulated.usda / extinguisher_rigid.usda 所在目录")
parser.add_argument("--door_stiffness", type=float, default=2.0,
                    help="松开阶段门/盖回到关闭位置的弹簧刚度 (N*m/rad)，模拟门扣")
parser.add_argument("--no_extinguisher", action="store_true", help="不加载灭火器")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
simulation_app = AppLauncher(args).app

import math  # noqa: E402

import torch  # noqa: E402

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.actuators import ImplicitActuatorCfg  # noqa: E402
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg  # noqa: E402
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg  # noqa: E402
from isaaclab.utils import configclass  # noqa: E402

from isaac_so_arm101.robots.nero_description.nero import NERO_CFG  # noqa: E402

# 消防箱放在机械臂正前方 0.40 m，绕 Z 转 -90°，让门朝向机械臂（IsaacLab 四元数顺序 wxyz）
CAB_POS = (0.40, 0.0, 0.0)
YAW_M90 = (math.sqrt(0.5), 0.0, 0.0, -math.sqrt(0.5))
# 灭火器在原场景里相对箱体的 x 偏移 -0.0608 / +0.0742，转 -90° 后变成世界系的 y 偏移
EXT_A_POS = (CAB_POS[0], 0.0608, 0.0)
EXT_B_POS = (CAB_POS[0], -0.0742, 0.0)

STIFF_FORCE = 20.0  # 脚本强制开关门时用的刚度


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

    robot: ArticulationCfg = NERO_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    cabinet = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Cabinet",
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{args.overrides}/cabinet_articulated.usda",
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                fix_root_link=True, enabled_self_collisions=False
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(pos=CAB_POS, rot=YAW_M90, joint_pos={".*": 0.0}),
        actuators={
            "doors": ImplicitActuatorCfg(
                joint_names_expr=[".*"],
                stiffness=args.door_stiffness,
                damping=0.3,
                effort_limit_sim=50.0,
            )
        },
    )

    ext_a = ext_cfg("Extinguisher_A", EXT_A_POS)
    ext_b = ext_cfg("Extinguisher_B", EXT_B_POS)


# (持续秒数, 顶盖目标角度°, 前门目标角度°, 刚度, 说明)
SCHEDULE = [
    (3.0, 0.0, 0.0, None, "松开：看关闭状态是否稳定"),
    (4.0, -90.0, 0.0, STIFF_FORCE, "顶盖掀开到 90°"),
    (4.0, 0.0, 0.0, STIFF_FORCE, "顶盖关回"),
    (4.0, 0.0, 90.0, STIFF_FORCE, "前门翻开到 90°"),
    (4.0, 0.0, 0.0, STIFF_FORCE, "前门关回"),
    (3.0, -170.0, 170.0, STIFF_FORCE, "两个都开到接近极限"),
    (4.0, 0.0, 0.0, None, "松开：看门在重力和门扣弹簧下怎么动"),
]


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
    print("[INFO] cabinet joints:", cab.joint_names, " bodies:", cab.body_names)
    print("[INFO] robot joints:", robot.joint_names)
    print("[INFO] robot bodies:", robot.body_names)
    # 诊断信息：自碰撞开关、PhysX 里实际的关节刚度和限位
    import omni.usd
    from pxr import PhysxSchema, UsdPhysics
    stage = omni.usd.get_context().get_stage()
    for prim in stage.Traverse():
        if prim.GetPath().pathString.startswith("/World/envs/env_0/Cabinet") and prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            sc = PhysxSchema.PhysxArticulationAPI(prim).GetEnabledSelfCollisionsAttr().Get()
            print(f"[INFO] cab articulation root: {prim.GetPath()}  enabledSelfCollisions={sc}")
    print("[INFO] cab limits (rad):", cab.data.joint_pos_limits[0].tolist())
    lid_id = cab.find_joints("top_lid_joint")[0][0]
    door_id = cab.find_joints("front_door_joint")[0][0]
    exts = [scene[k] for k in ("ext_a", "ext_b") if not args.no_extinguisher]

    dt = sim.get_physics_dt()
    step, phase, phase_t = 0, -1, 1e9
    while simulation_app.is_running():
        # 切换阶段
        if phase < 0 or phase_t >= SCHEDULE[phase][0]:
            phase = (phase + 1) % len(SCHEDULE)
            phase_t = 0.0
            dur, lid_deg, door_deg, stiff, note = SCHEDULE[phase]
            k = args.door_stiffness if stiff is None else stiff
            cab.write_joint_stiffness_to_sim(torch.full_like(cab.data.joint_stiffness, k))
            tgt = torch.zeros_like(cab.data.joint_pos)
            tgt[:, lid_id] = math.radians(lid_deg)
            tgt[:, door_id] = math.radians(door_deg)
            cab.set_joint_position_target(tgt)
            print(f"\n[PHASE {phase}] {note} (lid {lid_deg}°, door {door_deg}°, k={k})")
            print("    physx stiffness:", cab.root_physx_view.get_dof_stiffnesses()[0].tolist())

        robot.set_joint_position_target(robot.data.default_joint_pos)
        scene.write_data_to_sim()
        sim.step()
        scene.update(dt)
        phase_t += dt
        step += 1

        if step % 50 == 0:
            q = cab.data.joint_pos[0]
            tq = cab.data.applied_torque[0]
            msg = (f"t={step * dt:6.2f}s  lid={math.degrees(q[lid_id]):7.1f}°  door={math.degrees(q[door_id]):7.1f}°"
                   f"  tau=({tq[lid_id]:.2f},{tq[door_id]:.2f})")
            for i, e in enumerate(exts):
                p = e.data.root_pos_w[0] - scene.env_origins[0]
                msg += f"  ext{i}=({p[0]:.3f},{p[1]:.3f},{p[2]:.3f})"
            print(msg)


if __name__ == "__main__":
    main()
    simulation_app.close()
