import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import re

PORT = 'COM7'
BAUD = 115200
MAX_POINTS = 50

raw_data   = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
alpha_data = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
beta_data  = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
ratio_data = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

current = {
    'alpha': 0, 'beta': 0, 'theta': 0,
    'ratio': 0, 'panic_count': 0,
    'status': 'WAITING...', 'valid': False,
    'trial': 0
}

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print("Connected to " + PORT)
except Exception as e:
    print("ERROR: Could not open " + PORT + " - " + str(e))
    print("Change PORT variable to your COM port number")
    input("Press Enter to exit...")
    exit()

def parse_line(line):
    line = line.strip()
    try:
        if re.match(r'^\d+$', line):
            raw_data.append(int(line))
            return
        if 'Alpha' in line:
            v = re.search(r':\s*([\d.]+)', line)
            if v: current['alpha'] = float(v.group(1))
        elif 'Beta' in line and 'Alpha' not in line:
            v = re.search(r':\s*([\d.]+)', line)
            if v: current['beta'] = float(v.group(1))
        elif 'Theta' in line:
            v = re.search(r':\s*([\d.]+)', line)
            if v: current['theta'] = float(v.group(1))
        elif 'Ratio' in line:
            v = re.search(r':\s*([\d.]+)', line)
            if v:
                current['ratio'] = float(v.group(1))
                ratio_data.append(current['ratio'])
                alpha_data.append(current['alpha'])
                beta_data.append(current['beta'])
                current['trial'] += 1
        elif 'Panic count' in line:
            v = re.search(r':\s*(\d+)', line)
            if v: current['panic_count'] = int(v.group(1))
        elif 'Signal valid' in line:
            current['valid'] = 'YES' in line
        elif 'STATUS' in line:
            if 'PANIC'     in line: current['status'] = 'PANIC!!!'
            elif 'STRESS'  in line: current['status'] = 'STRESS RISING'
            elif 'CALM'    in line: current['status'] = 'CALM'
            elif 'HEADBAND' in line: current['status'] = 'HEADBAND OFF'
    except Exception:
        pass

plt.style.use('dark_background')
fig = plt.figure(figsize=(14, 8))
fig.patch.set_facecolor('#0d1117')
fig.suptitle('EEG Panic Detector - CyberNuts', fontsize=14, color='white', fontweight='bold', y=0.98)

ax_raw    = fig.add_subplot(3, 3, (1, 2))
ax_ratio  = fig.add_subplot(3, 3, (4, 5))
ax_bands  = fig.add_subplot(3, 3, 3)
ax_status = fig.add_subplot(3, 3, 6)
ax_panic  = fig.add_subplot(3, 3, (7, 9))

for ax in [ax_raw, ax_ratio, ax_bands, ax_status, ax_panic]:
    ax.set_facecolor('#161b22')
    for spine in ax.spines.values():
        spine.set_color('#30363d')

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.subplots_adjust(hspace=0.45, wspace=0.35)

def update(frame):
    try:
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore')
            parse_line(line)
    except Exception:
        pass

    ax_raw.cla()
    ax_raw.set_facecolor('#161b22')
    ax_raw.plot(list(raw_data), color='#58a6ff', linewidth=1)
    ax_raw.set_title('Live EEG Signal', color='#8b949e', fontsize=9, pad=4)
    ax_raw.set_ylim(0, 4096)
    ax_raw.tick_params(colors='#8b949e', labelsize=7)
    ax_raw.set_ylabel('ADC value', color='#8b949e', fontsize=7)
    for sp in ax_raw.spines.values(): sp.set_color('#30363d')

    ax_ratio.cla()
    ax_ratio.set_facecolor('#161b22')
    rlist = list(ratio_data)
    ax_ratio.plot(rlist, color='#58a6ff', linewidth=1.5)
    ax_ratio.axhline(y=1.5, color='#f85149', linewidth=1, linestyle='--', label='Panic 1.5')
    ax_ratio.axhline(y=1.2, color='#d29922', linewidth=1, linestyle=':', label='Stress 1.2')
    ax_ratio.fill_between(range(len(rlist)), rlist, 1.5,
                          where=[r > 1.5 for r in rlist],
                          alpha=0.3, color='#f85149')
    ax_ratio.set_title('Beta/Alpha Ratio', color='#8b949e', fontsize=9, pad=4)
    ax_ratio.set_ylim(0, max(4, max(rlist) + 0.5) if rlist else 4)
    ax_ratio.tick_params(colors='#8b949e', labelsize=7)
    ax_ratio.legend(fontsize=6, loc='upper left', facecolor='#161b22', labelcolor='#8b949e', edgecolor='#30363d')
    for sp in ax_ratio.spines.values(): sp.set_color('#30363d')

    ax_bands.cla()
    ax_bands.set_facecolor('#161b22')
    bands  = ['Theta\n4-8Hz', 'Alpha\n8-13Hz', 'Beta\n13-30Hz']
    values = [current['theta'], current['alpha'], current['beta']]
    colors = ['#7c3aed', '#2563eb', '#d97706']
    maxv = max(values) if max(values) > 0 else 1
    bars = ax_bands.barh(bands, [v / maxv * 100 for v in values], color=colors, alpha=0.85, height=0.5)
    ax_bands.set_title('Band Powers', color='#8b949e', fontsize=9, pad=4)
    ax_bands.set_xlim(0, 120)
    ax_bands.tick_params(colors='#8b949e', labelsize=7)
    for bar, val in zip(bars, values):
        ax_bands.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                      '{:.0e}'.format(val), va='center', color='#8b949e', fontsize=6)
    for sp in ax_bands.spines.values(): sp.set_color('#30363d')

    ax_status.cla()
    ax_status.axis('off')
    status = current['status']
    if status == 'PANIC!!!':
        scolor, sbg = '#f85149', '#3d1a18'
    elif status == 'STRESS RISING':
        scolor, sbg = '#d29922', '#2d2208'
    elif status == 'CALM':
        scolor, sbg = '#3fb950', '#0d2318'
    else:
        scolor, sbg = '#8b949e', '#161b22'
    ax_status.set_facecolor(sbg)
    ax_status.text(0.5, 0.75, status, transform=ax_status.transAxes,
                   ha='center', va='center', fontsize=12, fontweight='bold', color=scolor)
    ax_status.text(0.5, 0.52, 'Ratio: {:.2f}'.format(current['ratio']),
                   transform=ax_status.transAxes, ha='center', va='center', fontsize=10, color='#8b949e')
    ax_status.text(0.5, 0.32, 'Panic: {}/3'.format(current['panic_count']),
                   transform=ax_status.transAxes, ha='center', va='center', fontsize=10, color='#8b949e')
    ax_status.text(0.5, 0.14, 'Trial #{}'.format(current['trial']),
                   transform=ax_status.transAxes, ha='center', va='center', fontsize=8, color='#484f58')
    ax_status.set_title('Status', color='#8b949e', fontsize=9, pad=4)
    for sp in ax_status.spines.values(): sp.set_color('#30363d')

    ax_panic.cla()
    ax_panic.set_facecolor('#161b22')
    pct = (current['panic_count'] / 3.0) * 100
    bar_color = '#f85149' if pct >= 100 else '#d29922' if pct > 0 else '#3fb950'
    ax_panic.barh(['Panic confidence'], [100], color='#21262d', alpha=0.5, height=0.4)
    ax_panic.barh(['Panic confidence'], [pct], color=bar_color, alpha=0.85, height=0.4)
    ax_panic.axvline(x=100, color='#f85149', linewidth=1.5, linestyle='--')
    ax_panic.set_xlim(0, 110)
    ax_panic.set_title('Panic Confidence  (100% = alert triggered)', color='#8b949e', fontsize=9, pad=4)
    ax_panic.text(pct + 1, 0, '{:.0f}%'.format(pct), va='center', color=bar_color, fontsize=12, fontweight='bold')
    ax_panic.tick_params(colors='#8b949e', labelsize=8)
    for sp in ax_panic.spines.values(): sp.set_color('#30363d')

    return []

ani = animation.FuncAnimation(fig, update, interval=200, blit=False, cache_frame_data=False)
plt.show()
ser.close()
