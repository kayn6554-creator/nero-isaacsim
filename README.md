# nero-isaacsim

在实验室工作站 102（192.168.1.102，RTX 4090）上，用 **Isaac Sim 5.1.0 + IsaacLab 2.3.0** 搭建 NERO 机械臂的仿真环境，并接入消防箱数字资产。

当前进度：环境已装好，NERO 场景能跑、能推流看画面，消防箱资产能加载进场景。消防箱门的关节控制和鼠标交互演示还在验证中。

**新人请直接看 [KANBAN.md](KANBAN.md)**，里面按顺序列出了每一步要敲的命令、要做的操作，以及正常情况下应该看到什么。

## 目录

```
nero-isaacsim/
├── KANBAN.md                  进度看板 + 逐步操作手册（从这里开始）
├── scripts/
│   ├── env.sh                 每个新终端先 source 它
│   ├── copy_gcf_project.sh    复制 gcf 的 NERO 仿真项目（isaac_so_arm101）
│   ├── setup_env.sh           一次性安装 Isaac Sim / IsaacLab / torch
│   ├── smoke_test.sh          无界面冒烟测试
│   ├── stream_lift.sh         推流运行 NERO lift 场景
│   ├── stream_isaacsim.sh     推流启动完整 Isaac Sim 界面（鼠标交互、录视频用）
│   ├── run_fire_test.sh       推流运行消防箱关节体测试
│   └── fire_cabinet_test.py   消防箱测试脚本（NERO + 消防箱 + 灭火器）
├── assets/
│   ├── README.md              原始资产怎么放
│   └── overrides/             给原始资产加物理设置的覆盖层（不改原文件）
│       ├── cabinet_articulated.usda
│       └── extinguisher_rigid.usda
└── docs/
    ├── troubleshooting.md     踩过的坑和解决办法
    └── camera_params.md       真机两个 D405 相机的内参/外参（仿真里摆相机用）
```

## 依赖的外部内容（不在本仓库里）

| 内容 | 位置 | 说明 |
|---|---|---|
| NERO 仿真项目 | `/data/gcf/workspace/isaac_so_arm101` | gcf 基于 [smalleha/isaac_so_arm101](https://github.com/smalleha/isaac_so_arm101) 改的，含 NERO 的 URDF/USD、reach/lift 任务。用 `copy_gcf_project.sh` 复制一份到本仓库下 |
| 消防箱资产 | `Fire_equipment.zip` | 放置方法见 [assets/README.md](assets/README.md) |
| Isaac Sim 离线资产包 | `/data/gcf/isaac_assets` | 5.1.0 完整资产（458 GB），暂时没用到 |

## 环境版本

| 项 | 版本 |
|---|---|
| 系统 | Ubuntu 22.04.5，内核 6.8 |
| 显卡 / 驱动 | RTX 4090 24 GB / 580.126.09 |
| 内存 | 16 GB（偏小，Isaac Sim 建议 32 GB+） |
| Python | 3.11（uv 管理） |
| Isaac Sim / IsaacLab | 5.1.0 / 2.3.0（pip 安装） |
| torch / warp | 2.7.0+cu128 / 1.10.1 |
