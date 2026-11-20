# NERO 实时关节控制与消防箱手动交互

**用途：** 在一个 Isaac Sim 进程中加载 NERO、消防箱和灭火器；通过第二个 SSH 终端发送关节运动命令；同时保留 WebRTC 视图中的物理交互能力，便于手动拖动消防箱顶盖。

> 本方案不是“第二个 Python 程序重新启动 Isaac Sim”。TCP 控制服务运行在仿真进程内部，客户端只发送命令。

## 1. 场景与控制边界

- NERO 底座：(-0.60, 0.0, 0.0)。
- 消防箱： (0.40, 0.0, 0.0)，绕 Z 轴旋转 -90°。
- 仿真步长：0.01 s。
- 顶盖 actuator：stiffness=0.0，仅保留 damping；脚本不向顶盖发送位置目标。
- 前门 actuator：弱保持弹簧，默认 stiffness=2.0。
- 机械臂控制：只向 NERO 发送 set_joint_position_target()。
- 重力与碰撞：不在脚本中关闭。
- 鼠标交互：启动时请求启用 PhysX mouse interaction。

**实验边界：** NERO 的关节运动演示不等于机械臂已经通过接触成功开盖。手动拖动顶盖用于检查物理交互；自主推盖仍需独立设计接触轨迹和实验验证。

## 2. 文件

- scripts/fire_scene_control_server.py：唯一的 Isaac Sim 进程，加载场景、持续运行物理循环、监听本机 TCP 指令。
- scripts/nero_motion_client.py：轻量客户端，不导入 Isaac Sim、不创建 SimulationContext。
- scripts/run_fire_scene_control_server.sh：启动场景、WebRTC 和控制服务。
- 日志：/tmp/<用户名>_fire_scene_control_server.log。

## 3. 启动步骤

### 3.1 第一个 SSH 终端：启动仿真

登录工作站后执行：

\`\`\`bash
cd /data/panhe/isaac_nero
bash scripts/run_fire_scene_control_server.sh
\`\`\`

等待日志出现：

\`\`\`text
[SCENE] NERO + fire cabinet scene ready.
[CONTROL] Listening on 127.0.0.1:8765
\`\`\`

该终端保持运行，不要关闭，也不要再启动另一个 Isaac Sim。

### 3.2 Windows WebRTC 客户端：连接画面

连接工作站：

| 字段 | 值 |
|---|---|
| Server | 192.168.1.102 |
| Streaming port | 49100 |
| HTTP port | 47998 |

等待场景加载完成。应看到 NERO、消防箱和灭火器。

### 3.3 第二个 SSH 终端：发送运动指令

再开一个 PowerShell 窗口，重新 SSH 登录同一工作站：

\`\`\`powershell
ssh <工作站账号>@192.168.1.102
\`\`\`

进入仓库后发送命令：

\`\`\`bash
cd /data/panhe/isaac_nero

# 完整演示：前伸、回撤、左右摆动、回到初始姿态
.venv/bin/python scripts/nero_motion_client.py demo

# 单独前伸并保持
.venv/bin/python scripts/nero_motion_client.py forward

# 回撤到初始姿态
.venv/bin/python scripts/nero_motion_client.py back

# 左右摆动后回到初始姿态
.venv/bin/python scripts/nero_motion_client.py sway

# 回到初始姿态
.venv/bin/python scripts/nero_motion_client.py home

# 查看状态 / 紧急停止当前轨迹
.venv/bin/python scripts/nero_motion_client.py status
.venv/bin/python scripts/nero_motion_client.py stop
\`\`\`

客户端只发送一条 TCP 指令后退出；仿真服务仍持续运行，因此可以连续执行多条命令。

## 4. 手动拖动消防箱顶盖

1. 保持第一个终端中的仿真服务持续运行。
2. 等待 NERO 当前运动结束，必要时在第二个终端执行 stop。
3. 在 WebRTC 画面中选中顶盖附近的可交互刚体。
4. 使用鼠标拖动顶盖边缘，观察其是否绕铰链转动。
5. 松开鼠标后观察顶盖在重力和被动阻尼下的表现。

本脚本没有给 top_lid_joint 设置位置目标。若鼠标拖动无效，先检查 WebRTC 是否连接到本次新启动的服务端，以及日志中的 PhysX mouse interaction 提示；不要通过给顶盖添加脚本目标来“解决”鼠标交互问题。

## 5. 命令说明

| 命令 | 行为 |
|---|---|
| demo | 小幅前伸、回撤、左右摆动，最后回到 home |
| forward / reach | 进入小幅肩/肘组合姿态并保持 |
| back / retract | 回到配置的初始姿态 |
| sway / wave | joint1 左右小幅摆动后回 home |
| home | 平滑回到初始姿态 |
| stop | 中止当前轨迹，并保持当前关节姿态 |
| status | 输出当前关节位置与是否正在运动 |
| quit | 关闭仿真服务 |

默认每段轨迹用 2 秒插值，目标点保持 0.4 秒；joint1、joint2、joint3 的变化幅度为 0.12 rad，并依据运行时关节限位进行裁剪。前伸方向由当前 URDF 关节轴定义；首次观看时请确认视觉方向，如与预期相反，再调整 build_segments() 中 joint2/joint3 的正负号。

## 6. 停止服务

- 只停止当前运动：第二个终端执行 stop。
- 正常关闭仿真：第二个终端执行 quit，或在第一个终端按 Ctrl+C。
- 不要同时运行旧的 run_fire_scene_nero_motion_demo.sh、fire_lid_passive_test.py 和本服务；同一工作站同一时刻只保留一个 Isaac Sim 仿真进程。

## 7. 首次运行验收

- [ ] 场景服务启动，WebRTC 能看到 NERO 和消防箱。
- [ ] 第二个终端执行 demo，NERO 完成前伸、回撤、摆动。
- [ ] 执行 forward 后机械臂保持目标姿态，执行 back 后回到初始姿态。
- [ ] 执行 stop 能停止当前轨迹并保持姿态。
- [ ] 顶盖没有被脚本直接驱动。
- [ ] WebRTC 中可以手动拖动顶盖，松手后仍由物理仿真接管。

**验证纪律：** 文件已提交不代表工作站实测通过。首次在工作站运行后，应把实际结果、日志和截图补充到本节，再标记为已验证。
