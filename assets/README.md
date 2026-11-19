# 资产说明

## 原始资产（不入库）

`Fire_equipment.zip` 解压到本目录，得到 `assets/Fire equipment/`（解压方法见 KANBAN 第 7 步，**必须加 `LANG=C.UTF-8`**）：

```
Fire equipment/
├── fire equipment.usd            总场景：1 个消防箱 + 2 个灭火器 + 平行光（Omniverse 导出）
├── cabinet/
│   ├── cabinet.usdc              消防箱
│   └── textures/1.jpg, 1-1.jpg
└── extinguisher/
    ├── extinguisher.usdc         灭火器
    └── textures/灭火器3d模型_{basecolor,metallic,roughness,normal}.*
```

单位为米，Z 轴朝上。

| 物体 | 尺寸 | 原始物理设置 |
|---|---|---|
| 消防箱箱体 `_2` | 约 0.34 × 0.19 × 0.52 m | kinematic 刚体，SDF 碰撞（内部是空腔，能放东西） |
| 前门 `_1` | 薄板，z 0.29~0.47 m | 刚体，凸包碰撞；铰链在底边，绕 X 轴 0~175°，向外翻下 |
| 顶盖 `_3` | 罩在箱顶，z 0.46~0.52 m | 刚体，凸包碰撞；铰链在后沿，绕 X 轴 −175~0°，向上掀开 |
| 灭火器 ×2 | 高约 0.45 m，包围盒宽约 0.11 m | 刚体，凸包碰撞，约 5.7 万个面 |

注意事项：
- 消防箱资产里自带一块 50 × 50 m 的地面（`cabinet/GroundPlane`），放进别的场景时要停用；
- 原始资产都没有设质量，PhysX 会按默认密度来算；
- 灭火器的包围盒宽约 11 cm，NERO 的夹爪最大只能张开 10 cm，大概率夹不住瓶身，只能夹提把或瓶颈。

## 覆盖层 overrides/（入库）

用 USD 的引用（reference）叠在原始资产上，**不修改原文件**，按相对路径 `../Fire equipment/...` 引用。

- `cabinet_articulated.usda`：把消防箱改成 IsaacLab 能控制的关节体，具体改了哪些见 KANBAN 第 9 步；
- `extinguisher_rigid.usda`：给灭火器加 1 kg 的质量。

这两个文件供 IsaacLab 脚本使用：`scripts/fire_cabinet_test.py` 用于关节/驱动诊断，`scripts/fire_lid_passive_test.py` 用于顶盖被动基线验证。在 Isaac Sim 界面里做鼠标交互演示，直接打开原始的 `fire equipment.usd` 就行。
