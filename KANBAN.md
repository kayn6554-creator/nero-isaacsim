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
| 9 | IsaacLab 关节体测试（脚本开关门） | 🟡 待验证：资产已识别为关节体，但门不动，已出修复版待重跑 |
| 10 | 鼠标交互 + 录制演示视频 | 🟡 待验证 |
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

## 第 9 步　IsaacLab 关节体测试（脚本开关门）　🟡 待验证

**做什么**：用脚本搭一个场景：NERO、消防箱（放在机械臂正前方 0.4 m，门朝向机械臂）、两个灭火器。机械臂不动，由脚本强制把顶盖掀开再关上、把前门翻开再关上，最后松开，用来检查门的关节、限位、碰撞对不对。

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

**当前状态（2026-11-11）**：
- ✅ 资产成功识别为关节体，关节名和刚体名都正确；
- ✅ 灭火器稳定地放在箱内（位置 z ≈ 0.02 m，没有掉落或飞出）；
- ❌ 门和盖完全不动（lid 一直停在 −1.2°，door 停在 0°）；
- 已经加了 DriveAPI 和碰撞过滤，修复版**还没有重跑验证**。重跑时看输出里的 `enabledSelfCollisions`、`physx stiffness`、`tau` 三项，可以判断问题出在哪一环。

---

## 第 10 步　鼠标交互 + 录制演示视频　🟡 待验证

**做什么**：录一段视频，展示消防箱资产可以交互：门能拉开，灭火器能拿出来。这一步不经过 IsaacLab，直接用 Isaac Sim 自带的物理鼠标拖拽功能。原始资产本身就带物理设置：箱体是 kinematic 固定的，门是刚体加铰链，灭火器是刚体，所以可以直接拿来演示。

**命令**：
```bash
cd /data/$USER/isaac_nero && source scripts/env.sh
pkill -u $USER -f fire_cabinet_test.py; pkill -u $USER -f zero_agent   # 先停掉其它仿真
bash scripts/stream_isaacsim.sh
```

**操作**：
1. 等终端里出现 `app ready`，然后用 WebRTC 客户端连接；
2. 菜单 **File → Open**，打开 `/data/<你的账号>/isaac_nero/assets/Fire equipment/fire equipment.usd`；
3. 在 Windows 上按 **Win + Alt + R** 开始录屏（或者用 OBS 录 WebRTC 客户端的窗口）；
4. 点左侧工具栏的 **▶ Play**，开始物理仿真；
5. 按住 **Shift**，用鼠标左键拖动顶盖、前门、灭火器；
6. 演示完点 **■ Stop**（场景会复位），然后停止录屏。

**期望现象**：Play 之后，物体在 Shift + 拖动下会跟着鼠标走：顶盖绕后沿往上掀，前门绕底边往外翻，灭火器可以从箱子里拖出来。

**待确认**：
- `isaacsim.exp.full.streaming` 这个启动方式在 102 上还没跑过；
- 如果拖不动，或者拖起来太轻、乱飞，可以在 **Edit → Preferences → Physics** 里调整鼠标交互的力度。

---

## 下一步（未开始）

1. 让 NERO 实际去开门：用键盘或主臂遥操作，或者用脚本给几个关键位姿；
2. 把两个仿真相机按真机参数摆放（参数见 [docs/camera_params.md](docs/camera_params.md)）；
3. 写仿真版的推理客户端，把 XR-1 系列模型（M0~M3、EF）接进来，作为推理链路的安全测试台；
4. 用主臂在仿真里遥操作采数据，导出成 LeRobot v3 格式。
