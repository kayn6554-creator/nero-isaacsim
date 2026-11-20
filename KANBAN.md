# 看板：NERO 仿真环境搭建 & 消防箱资产验证

## 进度一览

| 步骤 | 内容 | 状态 |
|---|---|---|
| 0 | Windows 端准备工具 | ✅ 完成 |
| 1 | SSH 登录 102 | ✅ 完成 |
| 2 | 获取本仓库 | ✅ 完成 |
| 3 | 复制 gcf 的 NERO 仿真项目 | ✅ 完成（2026-11-11） |
| 4 | 安装 Isaac Sim + IsaacLab 环境 | ✅ 完成（2026-11-11） |
| 5 | 无界面冒烟测试 | ✅ 通过（2026-11-11） |
| 6 | 推流查看 NERO 场景 | ✅ 通过（2026-11-11） |
| 7 | 放置消防箱资产 | ✅ 完成（2026-11-11） |
| 8 | 在界面里拖入消防箱查看 | ✅ 资产可加载、贴图正常、尺度正确 |
| 9 | IsaacLab 关节体结构与驱动诊断（历史脚本驱动测试） | 🗂️ 历史记录；仅供资产诊断，不用于正式实验 |
| 10 | 消防箱顶盖被动物理基线 | ✅ 通过（2026-11-13；四项验收全部达成） |
| 11 | NERO + 消防箱同场景实时控制服务 | ✅ 工作站实测通过（2026-11-20）|
| 12 | CPU PhysX 鼠标拖盖交互 | ✅ 工作站实测通过（2026-11-20）；录制视频待完成 |
| — | 机械臂开门、VLA 推理链路接入 | ⬜ 未开始 |

> 约定：下面每一步都分成 **做什么 → 命令/操作 → 正常现象 → 不正常怎么办**。命令块里的 `#` 开头是注释，不用敲。
> 每次打开新的 SSH 终端，先执行 `cd <仓库目录> && source scripts/env.sh`。

---

## 第 0 步　Windows 端准备工具

**做什么**：仿真跑在 102 上，你的 Windows 电脑只负责连接和看画面。

**操作**：
1. **PowerShell**：Windows 自带，用来 SSH 登录和 `scp` 传文件。
2. **Isaac Sim WebRTC Streaming Client**：在 NVIDIA Isaac Sim 文档的 Download 页面下载 **5.1 对应的 Windows 版**，用来看仿真画面。
3. （录视频时用）**Win + Alt + R**：Windows 自带的 Xbox Game Bar 录屏；或者安装 OBS。

**正常现象**：打开 WebRTC 客户端能看到 Server / Ports / Resolution 三栏和一个 Connect 按钮。

---

## 第 1 步　SSH 登录 102

**做什么**：以**自己的账号**登录工作站。

**操作**：在 PowerShell 里输入
```
ssh <你的账号>@192.168.1.102
```
输入密码（屏幕不显示字符，正常），回车。

**正常现象**：提示符变成 `<你的账号>@gzz2-MS-7D90:~$`。

**不正常怎么办**：
- 不要用 NoMachine 桌面里的终端跑仿真。那个桌面可能是别人（例如 `xr`）的会话，进程会挂在别人账号下，还会因为权限写不了文件。详见 [troubleshooting](docs/troubleshooting.md#1-nomachine-里跑仿真报-vkcreateraytracingpipelineskhr-failed)。

---

## 第 2 步　获取本仓库

**做什么**：把本仓库放到 `/data/<你的账号>/isaac_nero`，后面所有东西（环境、gcf 项目副本、资产）都放在这个目录下。

**命令**：
```bash
conda deactivate 2>/dev/null; conda deactivate 2>/dev/null
cd /data/$USER
git clone <本仓库地址> isaac_nero
cd isaac_nero
source scripts/env.sh
echo $NERO_SIM_ROOT
```

**正常现象**：最后一行打印出 `/data/<你的账号>/isaac_nero`。

---

## 第 3 步　复制 gcf 的 NERO 仿真项目

**做什么**：gcf 已经在 IsaacLab 里配好了 NERO（URDF→USD、关节驱动参数、头部和腕部相机、reach/lift 任务），而且他本地有很多改动没推到 GitHub。所以要复制他**本地**这份，不能用 GitHub 上的版本。脚本只读取他的目录，不会修改它。

**命令**：
```bash
cd /data/$USER/isaac_nero && source scripts/env.sh
bash scripts/copy_gcf_project.sh
```

**正常现象**：
- 进度条到 100%，大约复制 440 MB；
- 最后打印 3 行 git 记录，第一行是 `copy from gcf isaac_so_arm101 (local)`。

**不正常怎么办**：出现 `Permission denied` 的话，说明你的账号读不了 gcf 的目录，找 gcf 开读权限。

> 注意：**不要在 gcf 的目录里执行 `uv run`**，它会改动 gcf 的环境。

---

## 第 4 步　安装 Isaac Sim + IsaacLab 环境

**做什么**：用 uv 建一个 Python 3.11 环境，装 Isaac Sim 5.1.0、IsaacLab 2.3.0、torch 2.7.0（cu128）。全程不需要 root，下载量约 15~20 GB，耗时几十分钟，所以放在 tmux 里跑，SSH 断开也不影响。

**命令**：
```bash
cd /data/$USER/isaac_nero && source scripts/env.sh
tmux new -s isaac_install
# 进入 tmux 后：
cd /data/$USER/isaac_nero && bash scripts/setup_env.sh
```
- 按 `Ctrl+B` 再按 `D` 可以退出 tmux，安装在后台继续。
- 用 `tmux attach -t isaac_install` 回来查看进度。
- 最后会问 `Do you accept the EULA? (Yes/No):`，输入 `yes` 回车。

**正常现象**：最后两行是
```
torch 2.7.0+cu128 True
warp 1.10.1
```

**不正常怎么办**：
| 报错 | 原因 | 处理 |
|---|---|---|
| `No module named 'pkg_resources'`（flatdict） | 新版 setuptools 删掉了这个模块 | 脚本里已经用 `build-constraints.txt` 限制 `setuptools<81`，确认这个文件生成了 |
| `Failed to download ... operation timed out` | NVIDIA 的源时快时慢 | 直接重跑 `bash scripts/setup_env.sh`，已经下载的包在缓存里 |
| 最后一行打印 `False` | 驱动或 CUDA 有问题 | 执行 `nvidia-smi`，驱动版本应该 ≥ 570（102 上是 580.126.09） |

---

## 第 5 步　无界面冒烟测试

**做什么**：不开画面，把 gcf 的 NERO 抓方块场景（`Isaac-Nero-Lift-Cube-v0`）跑 5 分钟，确认显卡、渲染、物理都正常。

**命令**：
```bash
cd /data/$USER/isaac_nero && source scripts/env.sh
bash scripts/smoke_test.sh
```
运行期间终端没有任何输出，等 5 分钟就行，**中途不要按 Ctrl+C**。

**正常现象**：
```
exit code: 124   (124 = 正常跑满 5 分钟后被 timeout 停掉，这是期望结果)
vkCreateRayTracing 报错次数: 0   (应为 0)
--- [Error]/Traceback（应为空）---
```
第一次启动要编译着色器、转换 URDF，大约需要 200 秒，之后会快很多。

**不正常怎么办**：
- `Failed to acquire exclusive lock to data store`：之前的仿真进程还没退出。执行 `ps -u $USER -o pid,etime,cmd | grep -E "zero_agent|isaac"` 找到它，再 `kill <PID>`。
- 日志里有 `Unresolved reference ... nero_gripper_physics.usd` 或 `link5/visuals`：这是 URDF 转换留下的视觉引用警告，不影响仿真，可以忽略。

---

## 第 6 步　推流查看 NERO 场景

**做什么**：仿真在 102 上以 headless 方式运行，同时把画面推送到 Windows 上的 WebRTC 客户端。

**命令**：
```bash
cd /data/$USER/isaac_nero && source scripts/env.sh
bash scripts/stream_lift.sh
```

**操作**：
1. 等终端里出现 `nvstPushStreamData timeout ... stream (nil)`。这条的意思是"已经在推流，但还没有客户端连上"，是正常的。第二次启动之后大约 40 秒就会出现。
2. 打开 WebRTC 客户端：Server 填 `192.168.1.102`，Ports 保持 `49100 / 47998`，Resolution 选 `1920 x 1080`，点 **Connect**。
3. 看完后，在 SSH 终端里按 `Ctrl+C` 停止仿真。

**正常现象**：客户端里出现完整的 Isaac Sim 界面：一台 NERO 装在黑色推车台面上，旁边有红、绿、蓝三个方块，机械臂保持初始姿态不动。

**不正常怎么办**：
- 一直黑屏：多半是在仿真准备好之前就连上了。在客户端菜单里点 **Connection → Disconnect**，再重新 Connect；还不行就把客户端关掉重开。
- 连不上：在 PowerShell 里执行 `Test-NetConnection 192.168.1.102 -Port 49100`，`TcpTestSucceeded` 应该是 `True`。
- 界面的基本操作：右键拖动是转视角，滚轮是缩放，选中物体后按 `F` 键可以让镜头对准它。

---

## 第 7 步　放置消防箱资产

**做什么**：把 `Fire_equipment.zip` 传到 102 上，解压到 `assets/Fire equipment/`。

**命令**：先在 Windows 的 PowerShell 里上传（路径改成 zip 在你电脑上的实际位置）：
```
scp "C:\Users\<你>\Downloads\Fire_equipment.zip" <你的账号>@192.168.1.102:/data/<你的账号>/isaac_nero/
```
然后在 SSH 终端里解压：
```bash
cd /data/$USER/isaac_nero/assets && source ../scripts/env.sh
LANG=C.UTF-8 unzip -o ../Fire_equipment.zip
find "Fire equipment" -type f | sort
```

**正常现象**：一共 9 个文件，灭火器的贴图显示成**中文文件名**，例如 `灭火器3d模型_basecolor.JPEG`。

**不正常怎么办**：如果文件名变成了 `#U706d#U706b...` 这种形式，说明解压时没加 `LANG=C.UTF-8`。USD 里引用的是中文名，这样贴图会找不到，灭火器就会显示成白模。删掉解压出来的目录，重新解压一次。

资产本身的说明见 [assets/README.md](assets/README.md)。

---

## 第 8 步　在界面里拖入消防箱查看

**做什么**：不写代码，直接在第 6 步的推流界面里把消防箱拖进场景，看看大小、贴图、比例对不对。

**操作**（先按第 6 步把推流界面打开）：
1. 左下角 **Content** 面板 → `My Computer` → `/data` → `<你的账号>` → `isaac_nero` → `assets` → `Fire equipment`。
2. 把 `fire equipment.usd` 用鼠标拖进中间的 3D 视口，松开。
3. 右上角 **Stage** 面板里会多出 `fire_equipment`。点中**它本身**（不要点它下面的子项），在右下角 **Property** → **Transform** 里改：
   - Translate：`0.4, 0, 0`
   - Orient：`0, 0, -90`
   改法是双击数字框，输入新值后按回车。

**正常现象**：一个红色的消防箱立在机械臂正前方的台面上，门朝向机械臂，高度大约 52 cm，和机械臂的比例协调。

**注意**：
- Stage 面板如果不小心关掉了，可以从菜单 **Window → Stage** 重新打开。
- **不要删** `World/GroundPlane` 下面的任何东西，那是场景本身的地面。
- 这个场景开着 **Fabric GPU** 模式，在界面里改了 USD 以后，物理和渲染不一定会同步。所以这一步只用来"看一眼"，正式的测试用第 9 步的脚本。

**结论（2026-11-11）**：资产能正常加载，贴图正常，单位和尺度正确，坐标轴 Z 朝上。

---

## 第 9 步　IsaacLab 关节体测试（历史脚本驱动诊断）　🗂️ 历史记录

> ⚠️ 本节保留的是早期资产关节/驱动诊断记录。fire_cabinet_test.py 会直接给消防箱关节写位置目标，只能用于理解历史诊断过程，不是 NERO 主动开盖实验，也不要作为当前正式演示入口。当前被动基线以第 10 步为准。

**做什么**：本阶段只用于检查消防箱能否作为 IsaacLab articulation 加载、关节名称/限位/方向是否正确，以及 USD 中的关节驱动是否响应。注意：`fire_cabinet_test.py` 会通过 `cab.set_joint_position_target(tgt)` 直接给顶盖和前门写入目标角度；它是资产/关节驱动诊断工具，不是 NERO 通过物理接触开门的正式实验。

原始资产不能直接给 IsaacLab 用，所以 `assets/overrides/cabinet_articulated.usda` 在**不改原文件**的前提下做了这些改动：
- 箱体改成关节体的根连杆（原来是 kinematic，关节体里不允许），运行时由 IsaacLab 用固定关节钉在世界上；
- 两扇门的关节重新定义为 `front_door_joint`（前门，底边铰链，0~175°）和 `top_lid_joint`（顶盖，后沿铰链，−175~0°）。原来的两个关节重名，而且连接的是网格而不是刚体；
- 给两个门关节加上角度驱动（DriveAPI），不加的话 IsaacLab 设置的刚度不起作用；
- 过滤顶盖和前门之间的碰撞：顶盖的凸包碰撞体和前门上沿重叠约 8 mm，不过滤的话两者会互相卡死；
- 停用资产自带的 50 m × 50 m 地面，补上质量（箱体 5 kg、前门 0.2 kg、顶盖 0.3 kg、灭火器 1 kg）。

**命令**：
```bash
cd /data/$USER/isaac_nero && source scripts/env.sh
bash scripts/run_fire_test.sh
```
等出现 `[PHASE 0]` 之后，再用 WebRTC 客户端连接（方法和第 6 步一样）。

**期望现象**：
```
[INFO] cab articulation root: /World/envs/env_0/Cabinet  enabledSelfCollisions=False
[INFO] cabinet joints: ['front_door_joint', 'top_lid_joint']  bodies: ['_2', '_1', '_3']
[PHASE 1] 顶盖掀开到 90° ...
    physx stiffness: [20.0, 20.0]
t= ...  lid=  -89.x°  door=   0.0°  tau=(...)
[PHASE 3] 前门翻开到 90° ...
t= ...  lid=   0.0°  door=  89.x°  ...
```
画面上应该看到：顶盖向上掀开，前门朝机械臂方向翻下来，两个灭火器一直待在箱子里不动。

**历史测试记录（2026-11-11；不是当前正式实验状态）**：
- ✅ 资产成功识别为关节体，关节名和刚体名都正确；
- ✅ 灭火器稳定地放在箱内（位置 z ≈ 0.02 m，没有掉落或飞出）；
- ❌ 门和盖完全不动（lid 一直停在 −1.2°，door 停在 0°）；
- 当时已加入 DriveAPI 和碰撞过滤，但该修复版未继续作为正式实验入口。此处保留历史排查记录；当前正式场景请使用第 10 步被动基线和第 11 步 NERO 关节运动 Demo。

---

## 第 10 步　消防箱顶盖被动物理基线测试　✅ 已完成（2026-11-13）

**做什么**：在 NERO、消防箱和两个灭火器同场景中，验证机器人不会意外碰到箱体；顶盖不接受脚本位置目标；前门和灭火器在基线状态下稳定。详细记录见 [docs/fire_lid_passive_baseline.md](docs/fire_lid_passive_baseline.md)。

**核心配置**：

| 项目 | 配置 |
|---|---|
| NERO 底座位置 | \`(-0.60, 0, 0)\`，只覆盖被动基线脚本，不改共享的 \`nero.py\` |
| 消防箱根节点 | \`(0.40, 0, 0)\`，绕 Z 轴 -90° |
| 环境数量 / 间距 | 1 / 2.0 m |
| 仿真物理步长 | 0.01 s |
| 顶盖 actuator | stiffness=0，damping 默认 0.3 |
| 前门 actuator | stiffness 默认 2.0，damping=0.3 |
| 灭火器 | 两个刚体，放在箱体内部 |

**运行命令**：

~~~bash
cd /data/panhe/isaac_nero
source scripts/env.sh
bash scripts/run_fire_lid_passive_test.sh
~~~

WebRTC Server 使用 \`192.168.1.102\`。完整日志保存在 \`/tmp/panhe_fire_lid_passive.log\`。

**验收结果**：

- ✅ NERO 与消防箱分离，不再搭在箱体/顶盖上；
- ✅ 被动测试脚本没有调用 \`cab.set_joint_position_target()\`；
- ✅ 顶盖 stiffness=0，仅保留阻尼；
- ✅ 前门保持关闭，两个灭火器稳定。

**重要边界**：本步骤只建立被动基线，不代表 NERO 已经主动打开顶盖。正式实验必须由 NERO 末端与顶盖边缘发生物理接触来产生开盖运动，不允许直接设置顶盖关节目标角度。

---

## 第 11 步　NERO + 消防箱同场景实时控制（CPU PhysX）　✅ 已完成（2026-11-20）

**做什么**：启动一个持续运行的 Isaac Sim 进程，同时加载 NERO、消防箱和两个灭火器。第二个 SSH 终端通过 TCP 客户端发送机械臂动作命令；WebRTC 负责显示画面和手动拖动顶盖。

**最小化验证原则：** 环境和资产已经安装完成后，不再执行额外 smoke test、重复资产探测或第二套 Isaac Sim 启动流程。日常只需要两个 SSH 终端、两条命令。

### 11.1 Windows 端登录工作站

在 Windows PowerShell 打开终端 A：

```powershell
ssh <你的工作站账号>@192.168.1.102
```

登录成功后，进入终端 A 的仓库目录并启动仿真：

```bash
cd /data/panhe/isaac_nero && bash scripts/run_fire_scene_control_server.sh
```

> 其他账号部署时，将路径替换为该账号实际仓库目录，例如 `/data/$USER/isaac_nero`。启动脚本会自动加载 `scripts/env.sh`，无需手动激活 Conda 或 venv。

### 11.2 确认仿真服务就绪

终端 A 保持运行，等待以下日志：

```text
[INFO] Simulation/PhysX device: cpu
[SCENE] NERO + fire cabinet scene ready.
[CONTROL] Listening on 127.0.0.1:8765
[WEBRTC] Connect to 192.168.1.102.
```

这里的 CPU 指 PhysX/仿真计算设备；RTX GPU 仍用于渲染和 WebRTC 推流。当前启动入口默认 CPU PhysX，这是为了兼容本场景的 Shift + 左键鼠标拖动物理交互。

**不要**在终端 B 再启动 Isaac Sim，也不要运行旧版 `run_fire_scene_nero_motion_demo.sh` 或 `fire_lid_passive_test.py`。

### 11.3 连接 WebRTC 画面

打开 Windows 上的 Isaac Sim WebRTC Streaming Client：

| 字段 | 值 |
|---|---|
| Server | `192.168.1.102` |
| Streaming port | `49100` |
| HTTP port | `47998` |

点击 Connect。应看到 NERO、消防箱和两个灭火器。

### 11.4 第二个 SSH 终端运行最小动作验证

在 Windows PowerShell 再开一个终端 B，重新登录同一工作站：

```powershell
ssh <你的工作站账号>@192.168.1.102
```

运行唯一一条动作验证命令：

```bash
cd /data/panhe/isaac_nero && .venv/bin/python scripts/nero_motion_client.py demo
```

**正常现象**：WebRTC 中 NERO 依次完成前伸、回撤、左右摆动并回到初始姿态。终端 B 的客户端收到服务端确认后退出；终端 A 的 Isaac Sim 和 TCP 服务继续运行。

### 11.5 其他控制命令

在终端 B 的仓库目录执行：

```bash
.venv/bin/python scripts/nero_motion_client.py forward
.venv/bin/python scripts/nero_motion_client.py back
.venv/bin/python scripts/nero_motion_client.py sway
.venv/bin/python scripts/nero_motion_client.py home
.venv/bin/python scripts/nero_motion_client.py status
.venv/bin/python scripts/nero_motion_client.py stop
```

| 命令 | 行为 |
|---|---|
| `demo` | 前伸、回撤、左右摆动，最后回 home |
| `forward` / `reach` | 进入肩/肘组合前伸姿态 |
| `back` / `retract` | 回到初始姿态 |
| `sway` / `wave` | joint1 左右摆动后回 home |
| `home` | 回到初始姿态 |
| `status` | 查看运动状态和当前关节位置 |
| `stop` | 中止当前轨迹并保持当前姿态 |
| `quit` | 关闭仿真服务 |

完整说明见 [docs/nero_live_control.md](docs/nero_live_control.md)。

---

## 第 12 步　CPU PhysX 下手动拖动消防箱顶盖　✅ 已完成（2026-11-20）

**做什么**：在第 11 步启动的同一个仿真进程中，使用 WebRTC 的 PhysX 鼠标交互拖动消防箱顶盖。不要额外启动完整 GUI 仿真或其他测试脚本。

**操作**：

1. 确认第 11 步终端 A 的服务仍在运行，启动日志显示 `Simulation/PhysX device: cpu`。
2. 等 NERO 当前动作结束；如果还在运动，在终端 B 执行：

   ```bash
   .venv/bin/python scripts/nero_motion_client.py stop
   ```

3. 在 WebRTC 画面中，将鼠标移到顶盖边缘。
4. 按住 **Shift + 鼠标左键**，拖动顶盖。
5. 观察顶盖绕铰链转动；松开鼠标后由重力和被动阻尼继续作用。

**为什么使用 CPU PhysX：** GPU Direct API 模式下，鼠标交互调用 PhysX `addTorque()` 曾触发：

```text
PxArticulationLink::addTorque():
it is illegal to call this method if
PxSceneFlag::eENABLE_DIRECT_GPU_API is enabled!
```

将仿真设备设为 CPU 后，当前工作站的鼠标拖盖操作已通过实测。服务端在 `AppLauncher.add_app_launcher_args(parser)` 后设置默认 `device=cpu`，因此无需额外参数，直接执行：

```bash
bash scripts/run_fire_scene_control_server.sh
```

**验收边界**：

- ✅ CPU PhysX 模式下鼠标可以拖动消防箱顶盖；
- ✅ 重力与碰撞保持启用；
- ✅ 顶盖 stiffness=0，脚本没有调用 `cabinet.set_joint_position_target()`；
- ✅ 机械臂的关节运动命令与手动拖盖在同一仿真进程中工作；
- ⬜ 演示视频录制尚未归档。

**注意：** NERO 关节运动 Demo 和人工鼠标拖盖只验证场景、关节控制和物理交互链路，不代表 NERO 已经通过末端接触自主打开消防箱。自主开盖仍需独立实验。

---

## 下一步（未开始）

1. 设计 NERO 主动开盖动作：比较夹持顶盖边缘与末端抵住边缘后向上推/掀两种方式；规划接近、接触、施力、开盖和撤离阶段。只能控制 NERO，不得直接给消防箱顶盖写关节目标；
2. 把两个仿真相机按真机参数摆放（参数见 [docs/camera_params.md](docs/camera_params.md)）；
3. 在低层接触动作可重复后，写仿真版推理客户端，把 XR-1 系列模型（M0~M3、EF）接入，作为推理链路的安全测试台；
4. 用主臂在仿真里遥操作采数据，导出成 LeRobot v3 格式。
