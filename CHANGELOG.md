# Changelog

## [0.1.0] - 2026-09-07

### Added

- 首次发布：按正弦横摇角计算 x、z 方向的 FDS 重力 RAMP，y 方向保持 0。
- 可修改频率、采样间隔、总时长、角幅值和重力加速度。
- 完整结果窗口、复制全部、首尾导航及控制台输出模式，不自动保存 FDS 结果文件。
- 从零开始并包含终点的时间序列，以及无效参数校验。
- Windows/Linux/macOS CI、单元测试、MIT 许可证、版本校验及带 SHA256 校验和的源码包。

### Defaults

- 频率 0.05 Hz、采样间隔 0.2 s、总时长 300 s、角幅值 ±10°、重力加速度 9.81 m/s²。

[0.1.0]: https://github.com/Mercury1219/fds-roll-gravity/releases/tag/v0.1.0
