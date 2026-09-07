import math
from decimal import Decimal

# ========= 可修改参数 =========
f = 0.05            # 横摇频率，Hz
dt = 0.2          # RAMP 采样时间步长，s
total_time = 300   # 总时长，s
theta0_deg = 10    # 横摇角幅值，度（即 ±10°）
g = 9.81           # 重力加速度，m/s²
output_mode = "window"  # "window"：完整结果窗口；"console"：控制台输出
# ==============================


def generate_fds(frequency, time_step, duration, amplitude_deg, gravity):
    """从 0 s 开始生成完整代码，仅返回字符串，不写入文件。"""
    if not all(math.isfinite(v) for v in
               (frequency, time_step, duration, amplitude_deg, gravity)):
        raise ValueError("参数必须为有限数值")
    if time_step <= 0 or duration <= 0 or gravity <= 0:
        raise ValueError("步长、总时长和重力加速度必须大于 0")
    if frequency < 0 or amplitude_deg < 0:
        raise ValueError("频率和角幅值不能为负数")

    theta0 = math.radians(amplitude_deg)
    # 避免浮点数累加误差，并确保包含总时长终点。
    step = Decimal(str(time_step))
    end = Decimal(str(duration))
    times = [i * step for i in range(int(end // step) + 1)]
    if times[-1] < end:
        times.append(end)
    decimals = max(2, -step.as_tuple().exponent, -end.as_tuple().exponent)

    lines = [
        f"! Roll: f={frequency:g} Hz, duration={duration:g} s, "
        f"amplitude={amplitude_deg:g} deg, dt={time_step:g} s",
        f"! Time range: 0 to {duration:g} s; RAMP records: {2 * len(times)}",
        f"&TIME T_END={end:f} /",
        "&MISC GVEC=1.0,0.0,1.0, RAMP_GX='ramp_x', RAMP_GZ='ramp_z' /",
        "",
    ]
    for t in times:
        theta = theta0 * math.sin(2 * math.pi * frequency * float(t))
        gx = gravity * math.sin(theta)
        gz = -gravity * math.cos(theta)
        gx = 0.0 if abs(gx) < 5e-9 else gx
        gz = 0.0 if abs(gz) < 5e-9 else gz
        lines.append(f"&RAMP ID='ramp_x', T={t:.{decimals}f}, F={gx:.8f} /")
        lines.append(f"&RAMP ID='ramp_z', T={t:.{decimals}f}, F={gz:.8f} /")
    return "\n".join(lines) + "\n"


def show_result(content):
    """显示全部结果，避免 IDE 控制台行数限制；不保存结果文件。"""
    import tkinter as tk
    from tkinter import scrolledtext, ttk

    root = tk.Tk()
    root.title("横摇重力 FDS 代码 — 完整结果")
    root.geometry("980x720")
    toolbar = ttk.Frame(root, padding=8)
    toolbar.pack(fill="x")
    status = tk.StringVar(value=f"0–{total_time:g} s | "
                               f"{content.count('&RAMP ')} 条 RAMP | 结果未保存为文件")
    box = scrolledtext.ScrolledText(root, wrap="none", font=("Consolas", 11))
    box.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    box.insert("1.0", content)
    box.configure(state="disabled")
    box.yview_moveto(0)

    def copy_all():
        root.clipboard_clear()
        root.clipboard_append(content)
        status.set("已复制全部代码（含 0 s 起点与总时长终点）")

    ttk.Button(toolbar, text="复制全部", command=copy_all).pack(side="left")
    ttk.Button(toolbar, text="回到开头", command=lambda: box.yview_moveto(0)).pack(side="left", padx=6)
    ttk.Button(toolbar, text="查看末尾", command=lambda: box.yview_moveto(1)).pack(side="left")
    ttk.Label(toolbar, textvariable=status).pack(side="left", padx=12)
    root.mainloop()


if __name__ == "__main__":
    result = generate_fds(f, dt, total_time, theta0_deg, g)
    if output_mode == "window":
        show_result(result)
    elif output_mode == "console":
        print(result, end="")
    else:
        raise ValueError('output_mode 只能为 "window" 或 "console"')
