# NERO 关节运动演示（消防箱同场景）

**状态：脚本已加入仓库；截至 2026-11-19 尚未在工作站 102 上完成本轮实测。** 明天首次演示前，先按本文进行完整运行验收，不要把“代码已提交”表述成“已验证通过”。

## 1. 目的与边界

本 Demo 用来证明：在 Isaac Sim / IsaacLab 中可以通过 Python 脚本加载 NERO，并向 NERO 的关节控制器发送连续、平滑的关节位置目标；同时在同一场景中显示消防箱和灭火器。

它复用 fire_lid_passive_test.py 已验证的场景布局：

| 对象 | 世界位置 / 配置 |
|---|---|
| NERO 底座 | (-0.60, 0.0, 0.0) |
| 消防箱 | (0.40, 0.0, 0.0)，绕 Z 轴旋转 -90° |
| 仿真步长 | 0.01 s |
| 顶盖 actuator | stiffness 0.0，仅保留 damping |
| 前门 actuator | 默认 stiffness 2.0，damping 0.3 |
| 灭火器 | 两个刚体，使用已有 override 资产 |

**控制边界非常重要：**

- 脚本只调用 robot.set_joint_position_target(...) 控制 NERO。
- 消防箱顶盖没有位置目标，顶盖 stiffness 为 0，仅保留被动阻尼。
- 前门沿用被动基线中的弱保持弹簧。
- 脚本没有调用 cabinet.set_joint_position_target(...)，也不以脚本角度驱动顶盖或前门。
- 本 Demo 只展示 NERO 的关节运动，不代表 NERO 已经通过接触打开消防箱。主动开盖仍是后续独立实验。

原有 scripts/fire_lid_passive_test.py 不会被本 Demo 修改，继续作为被动基线保留。

## 2. 文件

- scripts/fire_scene_nero_motion_demo.py：场景加载与 NERO 关节轨迹。
- scripts/run_fire_scene_nero_motion_demo.sh：headless + WebRTC 启动入口。

日志写入 /tmp/<username>_fire_scene_nero_motion_demo.log。

## 3. 前置条件

工作站上必须已经完成：

1. Isaac Sim 5.1.0 / IsaacLab 2.3.0 环境安装；
2. NERO 项目 isaac_so_arm101 已复制到仓库根目录并安装到 .venv；
3. 原始消防箱资产已放在 assets/Fire equipment/；
4. assets/overrides/cabinet_articulated.usda 和 extinguisher_rigid.usda 存在。

如果刚刚执行过 copy_gcf_project.sh，而安装环境时目录还不存在，需要重新执行一次 bash scripts/setup_env.sh，确保 NERO 包以 editable 方式安装。

## 4. 启动步骤

### 4.1 SSH 登录工作站

在 Windows PowerShell：

~~~powershell
ssh <工作站账号>@192.168.1.102
~~~

### 4.2 进入仓库并加载环境

~~~bash
cd /data/$USER/isaac_nero
source scripts/env.sh
~~~

### 4.3 启动 NERO + 消防箱场景

~~~bash
bash scripts/run_fire_scene_nero_motion_demo.sh
~~~

启动脚本会在工作站以 headless + WebRTC 模式运行 IsaacLab，并将日志保存到 /tmp/。

### 4.4 从 Windows WebRTC 客户端连接

| 客户端字段 | 值 |
|---|---|
| Server | 192.168.1.102 |
| Streaming port | 49100 |
| HTTP port | 47998 |
| Resolution | 1920 × 1080（可选） |

等待服务端开始推流后再连接。如果提前连接导致黑屏，先 Disconnect，再重新 Connect。

## 5. 默认运动序列

默认参数：

- 关节：joint1、joint2、joint3；
- 单关节最大偏移：0.18 rad（约 10.3°）；
- 每段插值时间：2.0 s；
- 每个目标保持：0.6 s；
- 循环次数：1。

每个关节依次执行：

1. 从当前姿态平滑移动到 home + amplitude；
2. 平滑移动到 home - amplitude；
3. 平滑返回 home；
4. 再处理下一个关节。

偏移会根据机器人运行时读取的关节限位做对称裁剪，并在关节可用范围不足时跳过该关节。脚本不会把默认的 0.18 rad 不加检查地直接写入所有关节。

预期日志示例（实际可用幅度可能因 URDF 关节限位而不同）：

~~~text
[DEMO] NERO joint-motion demo in the fire-cabinet scene.
[INFO] NERO joints: [...]
[INFO] cabinet lid stiffness=0; NO cabinet joint-position targets are sent.
[DEMO] Moving NERO to configured home pose.
[DEMO] Motion cycle 1/1.
[MOVE] joint1 +0.180 rad (... deg).
[MOVE] joint1 -0.180 rad (... deg).
[MOVE] joint1 return to home.
...
[DEMO] Finished successfully.
~~~

画面中应看到 NERO 机械臂分关节、连续地运动并返回初始姿态；消防箱、顶盖、前门和灭火器保持在同一场景中。

## 6. 可调参数

启动脚本会把额外参数转发给 Python 脚本：

~~~bash
# 更保守：只动 joint1，偏移 0.10 rad
bash scripts/run_fire_scene_nero_motion_demo.sh --joints joint1 --amplitude 0.10

# 三个关节运动更慢，便于观察
bash scripts/run_fire_scene_nero_motion_demo.sh --move-time 3.0 --hold-time 1.0

# 重复两轮
bash scripts/run_fire_scene_nero_motion_demo.sh --cycles 2

# 排查时暂时不加载灭火器
bash scripts/run_fire_scene_nero_motion_demo.sh --no-extinguisher
~~~

第一次实测建议先使用默认参数；如果观察到运动幅度过大或靠近消防箱，立即在 SSH 终端按 Ctrl+C，之后用 --amplitude 0.10 --joints joint1 缩小测试范围。

## 7. 停止与排查

- 正常情况下脚本完成运动序列后会保持 home 姿态数秒并退出，WebRTC 流随进程结束。
- 想提前停止，在启动脚本的 SSH 终端按 Ctrl+C。
- isaac_so_arm101 不存在或导入失败：回到 KANBAN 第 3 步复制 NERO 项目；复制完成后重新执行 bash scripts/setup_env.sh 安装 editable 包。
- 报缺少 cabinet_articulated.usda、extinguisher_rigid.usda 或原始 .usdc：检查 assets/README.md 和 KANBAN 第 7 步，确认原始资产目录名及大小写正确。
- Unknown NERO joint：检查启动日志打印的 NERO joints，再用 --joints 指定真实关节名。
- Failed to acquire exclusive lock：先停止当前用户遗留的 Isaac Sim / IsaacLab 进程；不要同时运行本 Demo、被动基线和完整 GUI 流程。
- WebRTC 黑屏：确认本次脚本已开始输出，客户端 Disconnect 后重新 Connect。

## 8. 明天的验收清单

- [ ] 工作站 102 上脚本成功启动，无 Python traceback。
- [ ] WebRTC 能看到 NERO、消防箱和灭火器。
- [ ] NERO 按顺序完成至少一个关节的正向、反向和 home 返回运动。
- [ ] 消防箱顶盖没有被脚本直接驱动；日志明确显示 lid stiffness 为 0。
- [ ] 运动过程中无明显抖动、穿模、碰撞或机器人脱离场景。
- [ ] 结束后能正常退出并重新启动被动基线脚本。

全部通过后，再把本文状态从“待实测”更新为“工作站已验证”，并记录实际运行日期、日志和画面截图。
