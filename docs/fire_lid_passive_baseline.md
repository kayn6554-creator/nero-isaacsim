# NERO 消防箱顶盖被动基线实验记录

> 日期：2026-11-13；状态：**四项验收全部通过**  
> 平台：工作站 102（192.168.1.102）/ Isaac Sim 5.1.0 / IsaacLab 2.3.0  
> 性质：仿真被动基线，不是 NERO 主动开盖实验。

## 0. 结论摘要

本次建立了 NERO + 消防箱 + 两个灭火器的被动物理基线。通过在本实验脚本中后移 NERO 底座、取消顶盖位置驱动，并将顶盖 actuator 配置为零刚度、仅保留阻尼，解决了机械臂初始搭在消防箱上的问题。

四项验收均由用户通过 WebRTC 画面检查并确认：

1. NERO 与消防箱分离，不再搭在箱体或顶盖上。
2. 被动测试脚本不调用消防箱的 \`cab.set_joint_position_target()\`，不直接给顶盖写入位置目标。
3. 顶盖 stiffness=0、仅保留 damping，处于被动物理状态。
4. 前门保持关闭，两个灭火器稳定留在场景中。

**本次只证明仿真场景基线可用，不证明 NERO 已经主动开盖。** 后续必须由 NERO 末端与顶盖发生物理接触，利用接触力和力矩完成开盖。

## 1. 实验定位与控制边界

原有 \`scripts/fire_cabinet_test.py\` 是资产/关节驱动诊断脚本。它会构造目标关节数组并调用：

~~~python
cab.set_joint_position_target(tgt)
~~~

旧脚本曾将顶盖驱动到约 -89.8°。这证明关节驱动链路能工作，但只是验证关节、限位、转轴和驱动，不是机器人开盖能力的证据。

正式实验约束：

- 可以控制 NERO 的关节、末端位姿或夹爪。
- 不允许通过脚本给消防箱顶盖设置目标角度。
- 顶盖运动必须来自 NERO 与顶盖边缘的物理接触。
- 顶盖角度、角速度、接触状态和视觉结果可作为观测与评估量，不能作为脚本直接控制目标。

新增的 \`fire_lid_passive_test.py\` 只保持 NERO 默认关节姿态，消防箱顶盖不接受脚本位置目标。

## 2. 运行环境与连接

| 项目 | 配置 |
|---|---|
| 主机 | \`gzz2-MS-7D90\` |
| SSH | \`panhe@192.168.1.102\` |
| GPU | NVIDIA GeForce RTX 4090 |
| OS | Ubuntu 22.04.5 |
| Python | 3.11 |
| Isaac Sim / IsaacLab | 5.1.0 / 2.3.0 |
| PyTorch | 2.7.0 + CUDA 12.8 |

仿真运行在工作站，Windows 端通过 Isaac Sim WebRTC Streaming Client 查看；不是在 Windows 本机运行物理仿真。本次关节和位姿数据来自 Isaac Sim / IsaacLab 仿真，不是真实 NERO 的实时反馈。

登录与环境准备：

~~~bash
ssh panhe@192.168.1.102
cd /data/panhe/isaac_nero
source scripts/env.sh
~~~

WebRTC Server 使用 \`192.168.1.102\`，Ports 使用工作站配置的 \`49100 / 47998\`。

## 3. 场景布局

### 3.1 NERO

为避免默认姿态下末端/夹爪与消防箱接触，本次只在被动基线脚本中覆盖 NERO 底座位置：

~~~python
ROBOT_BASE_POS = (-0.60, 0.0, 0.0)
~~~

使用 \`NERO_CFG.init_state.replace(pos=ROBOT_BASE_POS)\`，不修改共享的 \`nero.py\`，不会影响其他任务。该位置是**基线避让位置**，不是主动开盖任务的最终起始位置。

NERO 默认关节位置（顺序为 joint1~joint7、gripper_joint1、gripper_joint2）：

~~~text
[0, 0, 0, 2, 0, 0, 0, 0.05, -0.05]
~~~

### 3.2 消防箱

消防箱根节点位置为 \`(0.40, 0.0, 0.0)\`，绕世界 Z 轴旋转 -90°。IsaacLab 四元数顺序为 wxyz：

~~~python
CAB_POS = (0.40, 0.0, 0.0)
YAW_M90 = (sqrt(0.5), 0.0, 0.0, -sqrt(0.5))
~~~

加载 \`assets/overrides/cabinet_articulated.usda\`，配置 \`fix_root_link=True\`、\`enabled_self_collisions=False\`，两个门关节初始位置均为 0。

### 3.3 灭火器

两个灭火器作为独立刚体加载，使用与消防箱相同的朝向：

| 对象 | 初始位置 |
|---|---|
| Extinguisher A | \`(0.40, +0.0608, 0.0)\` |
| Extinguisher B | \`(0.40, -0.0742, 0.0)\` |

使用 \`assets/overrides/extinguisher_rigid.usda\`。原始模型和贴图保留在工作站 \`assets/Fire equipment/\`，不提交大体积原始资产包。

## 4. 消防箱关节结构与方向

探测确认关节名为 \`front_door_joint\`、\`top_lid_joint\`，刚体名为 \`_2\`、\`_1\`、\`_3\`。

### 前门

| 属性 | 值 |
|---|---|
| 类型 / 旋转轴 | Revolute / X |
| 限位 | 0° 至 +175°（约 0 至 3.0543 rad） |
| 铰链位置（箱体局部坐标） | \`(0, -0.09600294, 0.29206908)\` |

前门只能按当前关节定义向外翻开，不能向箱体内部翻开。

### 顶盖

| 属性 | 值 |
|---|---|
| 类型 / 旋转轴 | Revolute / X |
| 限位 | -175° 至 0°（约 -3.0543 至 0 rad） |
| 铰链位置（箱体局部坐标） | \`(0, 0.09140533, 0.5129813)\` |

顶盖绕箱体后沿铰链运动，负角度是资产定义的打开方向。主动开盖时应按此铰链位置、方向和限位规划接触点与施力方向。

## 5. 被动驱动参数

| 参数 | 默认值 | 作用 |
|---|---:|---|
| \`--door_stiffness\` | 2.0 N·m/rad | 前门弱关闭弹簧刚度 |
| \`--lid_damping\` | 0.3 N·m·s/rad | 顶盖被动阻尼 |

前门 actuator 匹配 \`front_door_joint\`，stiffness 默认 2.0、damping=0.3、effort_limit_sim=50.0。

顶盖 actuator 匹配 \`top_lid_joint\`，**stiffness=0.0**、damping 默认 0.3、effort_limit_sim=50.0。零刚度意味着没有位置恢复弹簧；阻尼只耗散角速度，不会把顶盖拉回某个目标角度，也不会主动开盖。顶盖响应由重力、碰撞、关节约束和外部接触共同决定。

## 6. 仿真循环与日志

- 环境数量：1；env_spacing：2.0 m。
- 物理步长：0.01 s（100 Hz）。
- NERO 每步保持 \`robot.data.default_joint_pos\`。
- Cabinet 不接收关节位置目标。
- 每 50 步（约 0.5 s）输出一次顶盖角度、角速度、applied torque，前门角度/角速度，以及两个灭火器相对环境原点的位置。

完整日志由包装脚本保存到 \`/tmp/panhe_fire_lid_passive.log\`。

## 7. 运行复现

~~~bash
cd /data/panhe/isaac_nero
source scripts/env.sh
bash scripts/run_fire_lid_passive_test.sh
~~~

也可直接运行：

~~~bash
.venv/bin/python scripts/fire_lid_passive_test.py --headless --livestream 2
~~~

启动后用 WebRTC 客户端连接工作站查看场景。结束时在运行脚本的 SSH 终端按 Ctrl+C。

可选参数：\`--door_stiffness 2.0\`、\`--lid_damping 0.3\`、\`--no_extinguisher\`、\`--overrides <目录>\`。

## 8. 验收结果（2026-11-13）

以下结果来自用户通过仿真画面检查并确认。本次没有形成完整数值误差或接触力统计，不虚构精确性能指标。

| 验收项 | 结果 | 说明 |
|---|---|---|
| NERO 与箱体分离 | ✅ 通过 | 后移基线底座后，机械臂不再搭在箱体/顶盖上 |
| 顶盖不被脚本直接驱动 | ✅ 通过 | 被动脚本无 Cabinet 位置目标调用 |
| 顶盖被动配置 | ✅ 通过 | stiffness=0，仅保留阻尼 |
| 前门与灭火器稳定 | ✅ 通过 | 前门关闭，两个灭火器稳定 |

**四项基线验收全部通过。**

## 9. 限制与注意事项

1. 所有位姿和关节数据均为仿真数据，不是真实 NERO 的传感器或关节反馈。
2. 本次验证的是场景基线和被动关节配置，不是主动开盖能力。
3. \`(-0.60, 0, 0)\` 是基线避让位置；主动任务需重新设计机器人与箱体相对位置。
4. 前门只能向外打开。
5. 原始消防箱资产在工作站本地 \`assets/Fire equipment/\`；不要提交原始资产包、虚拟环境、缓存、数据集或模型权重。
6. 启动前检查同一用户是否有其他 Isaac Sim 实例占用缓存/GPU；不要不加区分地结束其他用户进程。
7. URDF 转换时曾出现 \`nero_gripper_physics.usd\` unresolved reference 警告。本次场景正常加载并通过验收；未来若模型缺失或物理异常，仍需单独排查。

## 10. 下一阶段：NERO 主动开盖

1. 比较夹爪夹持顶盖边缘与末端抵住边缘后向上推/掀两种方式，结合夹爪最大开口、边缘厚度和接触面判断可行性。
2. 根据顶盖后沿铰链和负角度打开方向，规划从可达一侧接近顶盖前沿/侧缘的路径。
3. 将动作拆分为接近、对准、建立接触、施力、顶盖转动、撤离。
4. 用顶盖实际角度、角速度、接触状态和视觉结果定义成功，不以脚本目标角度作为成功依据。
5. 先验证可重复的低层接触动作，再接入 VLA 推理，并保留安全边界和失败恢复。

本被动基线脚本应保留为回归测试：每次修改 USD、关节驱动或场景布局后，先运行基线，确认场景稳定，再开展主动操作实验。
