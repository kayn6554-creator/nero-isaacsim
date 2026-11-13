#!/usr/bin/env bash
# 冒烟测试：无界面跑 gcf 的 NERO lift 场景 5 分钟，检查渲染和物理是否正常。
cd "$(dirname "$0")/.."
source scripts/env.sh
cd isaac_so_arm101
timeout 300 ../.venv/bin/zero_agent --task Isaac-Nero-Lift-Cube-v0 --num_envs 1 --enable_cameras --headless > /tmp/${USER}_smoke.log 2>&1
echo "exit code: $?   (124 = 正常跑满 5 分钟后被 timeout 停掉，这是期望结果)"
echo "vkCreateRayTracing 报错次数: $(grep -c -i vkCreateRayTracing /tmp/${USER}_smoke.log)   (应为 0)"
echo "--- [Error]/Traceback（应为空）---"
grep -i -E "\[Error\]|Traceback" /tmp/${USER}_smoke.log | head -10
