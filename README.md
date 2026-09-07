<h1 align="center">FDS Roll Gravity</h1>

<p align="center">为正弦横摇生成随时间变化的 FDS 重力分量。完整结果显示在可滚动窗口中，支持一键复制，不自动保存 FDS 结果文件。</p>

<p align="center">
  <a href="https://github.com/Mercury1219/fds-roll-gravity/releases/tag/v0.1.0"><img alt="Release v0.1.0" src="https://img.shields.io/badge/Release-v0.1.0-blue"></a>
  <a href="https://github.com/Mercury1219/fds-roll-gravity/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Mercury1219/fds-roll-gravity/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://www.python.org/downloads/"><img alt="Python 3.11–3.13" src="https://img.shields.io/badge/Python-3.11%E2%80%933.13-3776AB?logo=python&logoColor=white"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-green"></a>
</p>

## 功能

- 按给定横摇频率、角幅值和采样间隔生成 `MISC`、`TIME` 和全部 `RAMP` 行。
- 默认从 **0 s** 生成至 **300 s**，包含首尾端点；末端不足一个采样间隔时自动补齐终点。
- 可滚动的完整结果窗口支持“复制全部”“回到开头”“查看末尾”，避免 IDE 控制台截断前面的内容。
- 可切换为控制台输出；计算结果仅保存在内存，不自动创建 `.fds` 文件。
- 仅使用 Python 标准库。

## 快速开始

安装 Python 3.11–3.13。图形窗口需要 Tkinter；可先运行 `python -m tkinter` 检查。
Windows 和 macOS 的 python.org 安装程序通常包含 Tkinter；Ubuntu/Debian 系统 Python 可安装 `python3-tk`。
无图形桌面的环境请使用下述控制台模式。

下载 [最新 Release](https://github.com/Mercury1219/fds-roll-gravity/releases/latest) 的源码包并解压，或克隆：

```bash
git clone https://github.com/Mercury1219/fds-roll-gravity.git
cd fds-roll-gravity
python generate_roll_ramps.py
```

程序打开完整结果窗口。点击“复制全部”，即可将代码粘贴到已有 FDS 模型。

## 参数设置

直接修改 `generate_roll_ramps.py` 顶部：

```python
f = 0.05           # 横摇频率，Hz
dt = 0.2           # RAMP 采样时间间隔，s
total_time = 300   # 总时长，s
theta0_deg = 10    # 横摇角幅值，度（±10°）
g = 9.81           # 重力加速度，m/s²
output_mode = "window"  # "window" 或 "console"
```

当前默认采样间隔为 **0.2 s**。频率 0.05 Hz 对应 20 s 周期，300 s 覆盖 15 个周期。
每个分量生成 1501 个时间点，共 **3002 条 RAMP 记录**。
`dt` 是重力曲线采样间隔，不是 FDS 求解器的时间步长。

要在 IDE 运行结果框打印，将 `output_mode` 改为 `"console"`。
若控制台只显示从某个中间时刻开始的结果，检查 IDE 的输出行数/缓冲区限制，或使用默认窗口。
本脚本通过顶部变量配置，不提供 `--help` 或命令行参数解析。

也可在其他 Python 程序中调用，无需 Tkinter：

```python
from generate_roll_ramps import generate_fds

code = generate_fds(
    frequency=0.05,
    time_step=0.2,
    duration=300,
    amplitude_deg=10,
    gravity=9.81,
)
print(code, end="")
```

## 计算方法与 FDS 接入

横摇角及重力分量为：

```text
θ(t) = θ₀ sin(2πft)       θ₀ 在计算时转换为弧度
gx(t) =  g sin(θ(t))
gy(t) =  0
gz(t) = -g cos(θ(t))
```

生成的控制项和最初时间点为：

```fortran
&TIME T_END=300 /
&MISC GVEC=1.0,0.0,1.0, RAMP_GX='ramp_x', RAMP_GZ='ramp_z' /

&RAMP ID='ramp_x', T=0.00, F=0.00000000 /
&RAMP ID='ramp_z', T=0.00, F=-9.81000000 /
```

`F` 是对应 `GVEC` 分量的乘数，因此用 `GVEC=1.,0.,1.` 时，x、z 的 `F` 数值直接对应计算出的加速度分量；y 保持为 0。
时间变化使用 `T`。参见 [FDS 官方用户指南的 Gravity 章节](https://github.com/firemodels/fds/blob/master/Manuals/FDS_User_Guide/FDS_User_Guide.tex)。

1. 将控制项合并到模型已有的 `&MISC` 和 `&TIME`，避免重复设置。
2. 将全部 RAMP 行放在 `&TAIL /` 之前，替换已有同名曲线。
3. 数据假定模型从 0 s 开始；输出是输入片段，完整算例还需要网格、边界、火源等定义。

FDS 的点间线性插值保证分量连续，但不保证导数连续；插值区间内重力模长可能略小于设定值。可通过减小采样间隔检查精度。
此方法实现给定公式中的重力方向偏转，本身不设置船体网格运动或其他旋转惯性力。

## 验证与维护

```bash
python -m unittest discover -s tests -v
python scripts/release.py
```

CI 在 Windows、Ubuntu、macOS 上使用 Python 3.11 和 3.13，检查公式、时间范围、周期、参数校验、导入、源码语法、版本和源码包内容。
GUI 测试可在有桌面的环境中设置 `FDS_GUI_TEST=1` 后运行测试。
这些检查不等同于完整 FDS 求解器仿真。

详见 [贡献与发布说明](CONTRIBUTING.md)、[变更记录](CHANGELOG.md) 和 [安全报告](SECURITY.md)。

## 许可证

[MIT](LICENSE)。
