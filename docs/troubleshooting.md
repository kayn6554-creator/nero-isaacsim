# 踩坑记录

## 1. NoMachine 里跑仿真报 `vkCreateRayTracingPipelinesKHR failed`

**现象**：在 NoMachine 桌面里打开终端，运行不带 `--headless` 的仿真，终端里不停刷 `[carb.graphics-vulkan.plugin] vkCreateRayTracingPipelinesKHR failed`，而且看不到画面。

**原因**：NoMachine 连上的是虚拟桌面（`echo $DISPLAY` 输出 `:1001`），不经过 NVIDIA 显卡渲染，Isaac Sim 的 RTX 渲染器在上面开不了窗口。同样的命令加上 `--headless` 跑，这个报错是 0 次，说明显卡和驱动本身没问题。

**解决**：仿真一律加 `--headless --livestream 2` 运行，用 WebRTC 客户端看画面（KANBAN 第 6 步）。

另外，NoMachine 桌面里的终端可能是别人的账号（提示符是 `xr@...`）。在里面跑仿真，进程会挂在别人账号下，还会报 `Failed to create local file data store` 和 `unable to save the dictionary`，因为别人的账号写不了你的目录。**仿真只在自己账号的 SSH 终端里跑。**

## 2. `Failed to acquire exclusive lock to data store`

**原因**：之前的仿真进程没有退出，一直占着缓存锁（还占着 2 GB 左右的显存）。

**解决**：
```bash
ps -u $USER -o pid,etime,rss,cmd | grep -E "zero_agent|isaacsim|fire_cabinet" | grep -v grep
kill <PID>      # 5 秒后还在的话，用 kill -9 <PID>
```

## 3. 安装时报 `No module named 'pkg_resources'`

flatdict 4.0.1 构建时要用到 `pkg_resources`，而 setuptools ≥ 81 已经把它删掉了。安装时加上 `--build-constraints build-constraints.txt`，文件内容是 `setuptools<81`。`setup_env.sh` 里已经处理好了。

## 4. 安装时 `warp-lang` 下载超时

uv 会从 NVIDIA 的源去拉最新的 warp-lang（1.19.0，100 多 MB），经常超时，而且版本太新也不一定兼容。解决办法是先从清华源单独装 `warp-lang==1.10.1`（和 gcf 的环境保持一致），主安装时也固定这个版本。

## 5. git 报 `detected dubious ownership`

查看别人的仓库时，git 默认不信任别人的目录。在命令里临时加一个参数就行，不要改全局配置：
```bash
git -c safe.directory=/data/gcf/workspace/isaac_so_arm101 -C /data/gcf/workspace/isaac_so_arm101 status
```

## 6. 消防箱贴图文件名乱码（`#U706d#U706b...`）

zip 里的中文文件名，解压时需要指定 UTF-8：`LANG=C.UTF-8 unzip ...`。

## 7. 在 Isaac Sim 界面里改了物体，但物理或画面没有变化

gcf 的场景开着 **Fabric GPU** 模式，物理和渲染读的是 GPU 上的一份数据副本。在界面里改 USD，这份副本不一定会同步（左上角的面板会显示 "Properties not updated!"）。所以要做测试的场景，一律写在脚本或配置里，不要靠在界面上手动改。

## 8. 内存紧张

102 只有 16 GB 内存，Isaac Sim 启动后可用内存只剩 3~4 GB，swap 也会被用到。跑仿真的时候尽量别同时开别的大程序；如果感觉很卡，用 `free -h` 看一下内存。

## 9. 其它可以忽略的警告

- `Unresolved reference prim path ... nero_gripper_physics.usd`、`getAttributeCount called on non-existent path .../link5/visuals`：URDF 转换留下的视觉引用问题，不影响物理；
- `DLSS increasing input dimensions: Render resolution of (49, 49)...`：gcf 的相机分辨率是 84×84，太小触发的；
- `CPU performance profile is set to powersave`、`IOMMU is enabled`：系统设置相关的提示，不影响运行。
