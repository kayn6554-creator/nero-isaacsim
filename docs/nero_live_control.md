# NERO 实时关节控制与消防箱手动交互

**用途：** 在一个 Isaac Sim 进程中加载 NERO、消防箱和灭火器；通过第二个 SSH 终端发送关节运动命令；同时通过 WebRTC 画面手动拖动消防箱顶盖。

**工作站实测环境：** 192.168.1.102（工作目录 `/data/panhe/isaac_nero`），2026-11-20 验证通过。

> **最重要的结论：当前启动入口默认使用 CPU PhysX。** 使用 CPU 物理仿真后，WebRTC 中的 Shift + 鼠标左键拖动消防箱顶盖可以正常工作。RTX 4090 仍负责渲染和推流；切换的是仿真/物理计算设备，不是关闭 GPU 图形渲染。

> 本方案不是“第二个 Python 程序重新启动 Isaac Sim”。TCP 控制服务运行在唯一的 Isaac Sim 进程内部；第二个终端运行的客户端只发送命令。

## 0. 最小化验证：两个 SSH 终端、两条命令

如果工作站已经完成仓库、Python 环境、NERO 项目和消防箱资产的安装，日常验证只需要下面两条命令。**必须在两个独立的 SSH 终端中执行。**

### 终端 A：启动仿真场景、WebRTC 和控制服务

先在 Windows PowerShell 登录工作站：

```powershell
ssh <工作站账号>@192.168.1.102
```

登录成功后，在终端 A 执行这一条命令：

```bash
cd /data/panhe/isaac_nero && bash scripts/run_fire_scene_control_server.sh
```

等待日志出现以下内容：

```text
[INFO] Simulation/PhysX device: cpu
[SCENE] NERO + fire cabinet scene ready.
[CONTROL] Listening on 127.0.0.1:8765
[WEBRTC] Connect to 192.168.1.102.
```

终端 A 必须保持运行。不要关闭它，也不要在第二个终端再次启动 Isaac Sim。

### WebRTC：查看仿真画面

打开 Windows 上的 **Isaac Sim WebRTC Streaming Client**，填写：

| 字段 | 值 |
|---|---|
| Server | `192.168.1.102` |
| Streaming port | `49100` |
| HTTP port | `47998` |

点击 Connect，等待场景画面出现。应看到 NERO、消防箱和两个灭火器。

### 终端 B：发送最小运动验证命令

再打开一个 Windows PowerShell 窗口，重新 SSH 登录同一工作站：

```powershell
ssh <工作站账号>@192.168.1.102
```

在终端 B 执行这一条命令：

```bash
cd /data/panhe/isaac_nero && .venv/bin/python scripts/nero_motion_client.py demo
```

正常现象：WebRTC 画面中的 NERO 依次完成前伸、回撤、左右摆动并回到初始姿态；终端 B 返回命令执行结果后即可继续发送下一条命令。终端 A 中的仿真服务不会退出。

**这就是最小化验收：**
1. 终端 A 的启动日志出现 `Simulation/PhysX device: cpu`、`SCENE ready` 和 `Listening`；
2. 终端 B 的 `demo` 命令被接受，WebRTC 中能看到机械臂完成动作。

不需要额外运行 smoke test、单独启动第二个 Isaac Sim、重复检查资产或执行其他诊断脚本。

## 1. 登录、目录和环境说明

- 工作站地址：`192.168.1.102`。
- SSH 用户名：使用工作站分配给自己的账号；示例中的 `<工作站账号>` 需要替换。
- 当前项目目录：本工作站为 `/data/panhe/isaac_nero`。
- 其他账号部署时，通常将仓库放在 `/data/$USER/isaac_nero`，并相应替换下文路径。
- 启动脚本会自动 source `scripts/env.sh`，并使用仓库内的 `.venv`；启动服务时不需要手动激活 Conda 或 venv。
- 客户端命令直接调用 `.venv/bin/python`，也不需要额外 source 环境脚本。

首次部署或新机器尚未安装环境时，先按 [KANBAN.md](../KANBAN.md) 完成仓库获取、NERO 项目复制、Isaac Sim/IsaacLab 安装和消防箱资产放置。本文的两条最小命令适用于这些前置条件已经完成的工作站。

## 2. 场景与控制边界

- NERO 底座：`(-0.60, 0.0, 0.0)`。
- 消防箱：`(0.40, 0.0, 0.0)`，绕 Z 轴旋转 -90°。
- 仿真步长：0.01 s。
- 顶盖 actuator：stiffness=0.0，仅保留 damping；脚本不向顶盖发送位置目标。
- 前门 actuator：弱保持弹簧，默认 stiffness=2.0。
- 机械臂控制：只向 NERO 发送 `set_joint_position_target()`。
- 重力与碰撞：保持启用。
- 物理设备：默认 CPU PhysX，已在工作站上验证可配合鼠标拖动。
- 图形渲染与 WebRTC：仍由 Isaac Sim 的 GPU 渲染链路负责。
- 鼠标交互：启动时请求启用 PhysX mouse interaction。

**实验边界：** NERO 的关节运动演示不等于机械臂已经通过接触成功开盖。手动拖动顶盖用于检查资产的铰链和物理交互；自主推盖仍需独立设计接触轨迹并完成实验验证。

## 3. 常用控制命令

在终端 B（已经 SSH 登录工作站）执行：

```bash
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

# 查看状态 / 停止当前轨迹
.venv/bin/python scripts/nero_motion_client.py status
.venv/bin/python scripts/nero_motion_client.py stop
```

客户端只发送一条 TCP 指令后退出；仿真服务仍持续运行，因此可以连续执行多条命令。客户端通过 `127.0.0.1:8765` 连接服务端，所以必须在**同一台工作站的第二个 SSH 终端**执行，不能直接在 Windows 本机运行。

## 4. 手动拖动消防箱顶盖

1. 确认终端 A 的服务仍在运行，启动日志显示 `Simulation/PhysX device: cpu`。
2. 等待 NERO 当前运动结束；必要时在终端 B 执行 `stop`。
3. 在 WebRTC 画面中，将鼠标移动到消防箱顶盖边缘。
4. 按住 **Shift + 鼠标左键**，拖动顶盖边缘。
5. 观察顶盖是否绕后沿铰链转动；松开鼠标后，顶盖继续受重力和被动阻尼影响。

### 为什么必须使用 CPU PhysX

此前在 GPU Direct API 模式下使用 Shift + 左键拖动物体，会触发 PhysX 错误：

```text
PxArticulationLink::addTorque():
it is illegal to call this method if
PxSceneFlag::eENABLE_DIRECT_GPU_API is enabled!
```

问题来自 GPU Direct API 与当前 PhysX 鼠标拖动实现之间的兼容冲突，不是消防箱关节限位错误，也不是 NERO 关节运动脚本锁住了顶盖。

当前服务端在 `AppLauncher.add_app_launcher_args(parser)` 后将仿真设备默认设为 `cpu`，并在启动日志中打印：

```text
[INFO] Simulation/PhysX device: cpu
```

因此日常只需运行：

```bash
bash scripts/run_fire_scene_control_server.sh
```

不需要再手动追加 `--device cpu`。CPU 模式下的鼠标拖盖已在工作站 102 上实测通过。

## 5. 服务端实现与文件

- `scripts/fire_scene_control_server.py`：唯一的 Isaac Sim 进程，加载场景、运行物理循环、监听本机 TCP 指令；默认 CPU PhysX。
- `scripts/nero_motion_client.py`：轻量客户端，不导入 Isaac Sim、不创建 SimulationContext，只发送一条控制命令。
- `scripts/run_fire_scene_control_server.sh`：启动场景、WebRTC 和控制服务；自动加载环境脚本。
- 日志：`/tmp/<用户名>_fire_scene_control_server.log`。

## 6. 停止服务

- 只停止当前机械臂运动：终端 B 执行：

  ```bash
  .venv/bin/python scripts/nero_motion_client.py stop
  ```

- 正常关闭仿真服务：终端 B 执行：

  ```bash
  .venv/bin/python scripts/nero_motion_client.py quit
  ```

  或在终端 A 按 Ctrl+C。

- 不要同时运行旧版 `run_fire_scene_nero_motion_demo.sh`、`fire_lid_passive_test.py` 和本服务；同一工作站同一时刻只保留一个 Isaac Sim 仿真进程。

## 7. 工作站实测验收记录（2026-11-20）

以下项目已在工作站 `192.168.1.102` 实际验证：

- [x] 服务端正常启动，NERO、消防箱和灭火器加载成功。
- [x] WebRTC 能连接并显示场景。
- [x] 第二个 SSH 终端运行 `nero_motion_client.py demo`，NERO 能完成前伸、回撤和摆动。
- [x] CPU PhysX 模式下，WebRTC 中 Shift + 左键能够拖动消防箱顶盖。
- [x] NERO 关节运动期间，消防箱顶盖没有被脚本直接驱动；重力和碰撞保持启用。

**复现纪律：** 如果换了工作站、Isaac Sim/IsaacLab 版本或物理后端，应重新验收并记录环境差异。不要把当前工作站的成功结果直接当成所有机器上的保证。
