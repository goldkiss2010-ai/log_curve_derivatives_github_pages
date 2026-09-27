import math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUTDIR = Path(__file__).resolve().parent
OUTDIR.mkdir(exist_ok=True)
LN10 = math.log(10.0)
LN2 = math.log(2.0)

# Common comparison variable:
# r = scene-linear reflectance-like quantity, with r=0.18 treated as 18% grey.
# Canon's white paper uses reflection = 0.9 * Scene Linear, so its published x is r/0.9 here.

curves = {}

# ARRI LogC3, EI800, exposure-value parameters.
curves['ARRI LogC3 EI800'] = {
    'family': 'camera', 'kind': 'commonlog',
    'cut': 0.010591, 'a': 5.555556, 'b': 0.052272,
    'c': 0.247190, 'd': 0.385537, 'e': 5.367655, 'f': 0.092809,
    'join_domain': 'r', 'join': 0.010591,
    'low_type': 'linear', 'high_type': 'log10',
    'source_key': 'arri-logc3'
}

# ARRI LogC4.
b_lc4 = (1023.0 - 95.0) / 1023.0
c_lc4 = 95.0 / 1023.0
a_lc4 = (2.0**18 - 16.0) / 117.45
s_lc4 = 14.0 * LN2 * 2.0**(6.0 - 14.0*c_lc4/b_lc4) / (a_lc4*b_lc4)
t_lc4 = (2.0**(6.0 - 14.0*c_lc4/b_lc4) - 64.0) / a_lc4
curves['ARRI LogC4'] = {
    'family': 'camera', 'kind': 'logc4',
    'a': a_lc4, 'b': b_lc4, 'c': c_lc4, 's': s_lc4, 't': t_lc4,
    'join_domain': 'r', 'join': t_lc4,
    'low_type': 'linear extension (negative domain)', 'high_type': 'log2',
    'source_key': 'arri-logc4'
}

# Sony S-Log3.
curves['Sony S-Log3'] = {
    'family': 'camera', 'kind': 'slog3', 'cut': 0.01125,
    'join_domain': 'r', 'join': 0.01125,
    'low_type': 'linear', 'high_type': 'log10',
    'source_key': 'sony-slog3'
}

# Panasonic V-Log.
curves['Panasonic V-Log'] = {
    'family': 'camera', 'kind': 'vlog', 'cut': 0.01,
    'join_domain': 'r', 'join': 0.01,
    'low_type': 'linear', 'high_type': 'log10',
    'source_key': 'panasonic-vlog'
}

# FUJIFILM F-Log / F-Log2.
curves['FUJIFILM F-Log'] = {
    'family': 'camera', 'kind': 'commonlog',
    'cut': 0.00089, 'a': 0.555556, 'b': 0.009468,
    'c': 0.344676, 'd': 0.790453, 'e': 8.735631, 'f': 0.092864,
    'join_domain': 'r', 'join': 0.00089,
    'low_type': 'linear', 'high_type': 'log10',
    'source_key': 'fujifilm-flog'
}
curves['FUJIFILM F-Log2'] = {
    'family': 'camera', 'kind': 'commonlog',
    'cut': 0.000889, 'a': 5.555556, 'b': 0.064829,
    'c': 0.245281, 'd': 0.384316, 'e': 8.799461, 'f': 0.092864,
    'join_domain': 'r', 'join': 0.000889,
    'low_type': 'linear', 'high_type': 'log10',
    'source_key': 'fujifilm-flog2'
}

# Nikon N-Log. Published x is 10-bit code; normalized here by /1023.
curves['Nikon N-Log'] = {
    'family': 'camera', 'kind': 'nlog', 'cut': 0.328,
    'join_domain': 'r', 'join': 0.328,
    'low_type': 'cube root', 'high_type': 'natural log',
    'source_key': 'nikon-nlog'
}

# Canon white paper uses Scene Linear x and states reflection = Scene Linear * 0.9.
# Therefore, for the common reflectance-like r axis, u=r/0.9.
curves['Canon Log'] = {
    'family': 'camera', 'kind': 'canonlog',
    'join_domain': 'published scene-linear', 'join': 0.0,
    'low_type': 'signed log branch', 'high_type': 'signed log branch',
    'source_key': 'canon-log'
}
curves['Canon Log 2'] = {
    'family': 'camera', 'kind': 'canonlog2',
    'join_domain': 'published scene-linear', 'join': 0.0,
    'low_type': 'signed log branch', 'high_type': 'signed log branch',
    'source_key': 'canon-log'
}
curves['Canon Log 3'] = {
    'family': 'camera', 'kind': 'canonlog3',
    # positive join converted to reflectance-like common axis: 0.9 * 0.014
    'join_domain': 'r (positive join)', 'join': 0.9 * 0.014,
    'low_type': 'linear middle section', 'high_type': 'log10',
    'source_key': 'canon-log'
}

# RED Log3G10.
curves['RED Log3G10'] = {
    'family': 'camera', 'kind': 'log3g10',
    'join_domain': 'r', 'join': -0.01,
    'low_type': 'linear extension (negative domain)', 'high_type': 'log10',
    'source_key': 'red-log3g10'
}

# Comparison references (not camera log curves).
curves['CIE L* / 100'] = {
    'family': 'reference', 'kind': 'lab',
    'join_domain': 'Y/Yn', 'join': (6.0/29.0)**3,
    'low_type': 'linear', 'high_type': 'cube root',
    'source_key': 'cie-lab'
}
curves['Cineon reference'] = {
    'family': 'reference', 'kind': 'cineon',
    'join_domain': 'none', 'join': np.nan,
    'low_type': 'single smooth log with black offset', 'high_type': 'single smooth log with black offset',
    'source_key': 'kodak-cineon'
}


def encode(name, r):
    c = curves[name]
    r = np.asarray(r, dtype=float)
    k = c['kind']
    if k == 'commonlog':
        return np.where(r >= c['cut'], c['c']*np.log10(c['a']*r+c['b'])+c['d'], c['e']*r+c['f'])
    if k == 'logc4':
        return np.where(r >= c['t'], ((np.log2(c['a']*r+64.0)-6.0)/14.0)*c['b']+c['c'], (r-c['t'])/c['s'])
    if k == 'slog3':
        return np.where(r >= c['cut'], (420.0 + np.log10((r+0.01)/(0.18+0.01))*261.5)/1023.0,
                        (r*(171.2102946929-95.0)/0.01125 + 95.0)/1023.0)
    if k == 'vlog':
        return np.where(r >= 0.01, 0.241514*np.log10(r+0.00873)+0.598206, 5.6*r+0.125)
    if k == 'nlog':
        return np.where(r < 0.328, 650.0*np.cbrt(r+0.0075)/1023.0, (150.0*np.log(r)+619.0)/1023.0)
    if k == 'canonlog':
        u = r/0.9
        return np.where(u < 0.0, -0.45310179*np.log10(1.0-10.1596*u)+0.12512248,
                        0.45310179*np.log10(10.1596*u+1.0)+0.12512248)
    if k == 'canonlog2':
        u = r/0.9
        return np.where(u < 0.0, -0.24136077*np.log10(1.0-87.099375*u)+0.092864125,
                        0.24136077*np.log10(87.099375*u+1.0)+0.092864125)
    if k == 'canonlog3':
        u = r/0.9
        out = np.empty_like(u)
        m1 = u < -0.014
        m2 = (u >= -0.014) & (u <= 0.014)
        m3 = u > 0.014
        out[m1] = -0.36726845*np.log10(1.0-14.98325*u[m1])+0.12783901
        out[m2] = 1.9754798*u[m2]+0.12512219
        out[m3] = 0.36726845*np.log10(14.98325*u[m3]+1.0)+0.12240537
        return out
    if k == 'log3g10':
        a, b, off, g = 0.224282, 155.975327, 0.01, 15.1927
        z = r + off
        return np.where(z < 0.0, z*g, a*np.log10(z*b+1.0))
    if k == 'lab':
        delta = 6.0/29.0
        eps = delta**3
        ff = np.where(r > eps, np.cbrt(r), (841.0/108.0)*r + 4.0/29.0)
        return (116.0*ff - 16.0)/100.0
    if k == 'cineon':
        black_offset = 10.0**((95.0-685.0)/300.0)
        return (685.0 + 300.0*np.log10(r*(1.0-black_offset)+black_offset))/1023.0
    raise ValueError(name)


def d1(name, r):
    c = curves[name]
    r = np.asarray(r, dtype=float)
    k = c['kind']
    if k == 'commonlog':
        return np.where(r >= c['cut'], c['c']*c['a']/((c['a']*r+c['b'])*LN10), c['e'])
    if k == 'logc4':
        return np.where(r >= c['t'], c['b']*c['a']/(14.0*LN2*(c['a']*r+64.0)), 1.0/c['s'])
    if k == 'slog3':
        slope = (171.2102946929-95.0)/(0.01125*1023.0)
        return np.where(r >= 0.01125, 261.5/(1023.0*LN10*(r+0.01)), slope)
    if k == 'vlog':
        return np.where(r >= 0.01, 0.241514/(LN10*(r+0.00873)), 5.6)
    if k == 'nlog':
        return np.where(r < 0.328, 650.0/(3.0*1023.0)*(r+0.0075)**(-2.0/3.0), 150.0/(1023.0*r))
    if k == 'canonlog':
        u = r/0.9
        return np.where(u < 0.0,
                        0.45310179*10.1596/(LN10*(1.0-10.1596*u))/0.9,
                        0.45310179*10.1596/(LN10*(1.0+10.1596*u))/0.9)
    if k == 'canonlog2':
        u = r/0.9
        return np.where(u < 0.0,
                        0.24136077*87.099375/(LN10*(1.0-87.099375*u))/0.9,
                        0.24136077*87.099375/(LN10*(1.0+87.099375*u))/0.9)
    if k == 'canonlog3':
        u = r/0.9
        out = np.empty_like(u)
        m1 = u < -0.014
        m2 = (u >= -0.014) & (u <= 0.014)
        m3 = u > 0.014
        out[m1] = 0.36726845*14.98325/(LN10*(1.0-14.98325*u[m1]))/0.9
        out[m2] = 1.9754798/0.9
        out[m3] = 0.36726845*14.98325/(LN10*(1.0+14.98325*u[m3]))/0.9
        return out
    if k == 'log3g10':
        a, b, off, g = 0.224282, 155.975327, 0.01, 15.1927
        z = r + off
        return np.where(z < 0.0, g, a*b/(LN10*(z*b+1.0)))
    if k == 'lab':
        delta = 6.0/29.0
        eps = delta**3
        return np.where(r > eps, (116.0/100.0)*(1.0/3.0)*r**(-2.0/3.0), (116.0/100.0)*(841.0/108.0))
    if k == 'cineon':
        bo = 10.0**((95.0-685.0)/300.0)
        q = r*(1.0-bo)+bo
        return 300.0*(1.0-bo)/(1023.0*LN10*q)
    raise ValueError(name)


def d2(name, r):
    c = curves[name]
    r = np.asarray(r, dtype=float)
    k = c['kind']
    if k == 'commonlog':
        return np.where(r >= c['cut'], -c['c']*c['a']**2/(((c['a']*r+c['b'])**2)*LN10), 0.0)
    if k == 'logc4':
        return np.where(r >= c['t'], -c['b']*c['a']**2/(14.0*LN2*(c['a']*r+64.0)**2), 0.0)
    if k == 'slog3':
        return np.where(r >= 0.01125, -261.5/(1023.0*LN10*(r+0.01)**2), 0.0)
    if k == 'vlog':
        return np.where(r >= 0.01, -0.241514/(LN10*(r+0.00873)**2), 0.0)
    if k == 'nlog':
        return np.where(r < 0.328, -1300.0/(9.0*1023.0)*(r+0.0075)**(-5.0/3.0), -150.0/(1023.0*r**2))
    if k == 'canonlog':
        u = r/0.9
        fac = 1.0/(0.9**2)
        return np.where(u < 0.0,
                        0.45310179*10.1596**2/(LN10*(1.0-10.1596*u)**2)*fac,
                        -0.45310179*10.1596**2/(LN10*(1.0+10.1596*u)**2)*fac)
    if k == 'canonlog2':
        u = r/0.9
        fac = 1.0/(0.9**2)
        return np.where(u < 0.0,
                        0.24136077*87.099375**2/(LN10*(1.0-87.099375*u)**2)*fac,
                        -0.24136077*87.099375**2/(LN10*(1.0+87.099375*u)**2)*fac)
    if k == 'canonlog3':
        u = r/0.9
        out = np.empty_like(u)
        m1 = u < -0.014
        m2 = (u >= -0.014) & (u <= 0.014)
        m3 = u > 0.014
        fac = 1.0/(0.9**2)
        out[m1] = 0.36726845*14.98325**2/(LN10*(1.0-14.98325*u[m1])**2)*fac
        out[m2] = 0.0
        out[m3] = -0.36726845*14.98325**2/(LN10*(1.0+14.98325*u[m3])**2)*fac
        return out
    if k == 'log3g10':
        a, b, off = 0.224282, 155.975327, 0.01
        z = r + off
        return np.where(z < 0.0, 0.0, -a*b*b/(LN10*(z*b+1.0)**2))
    if k == 'lab':
        delta = 6.0/29.0
        eps = delta**3
        return np.where(r > eps, -(116.0/100.0)*(2.0/9.0)*r**(-5.0/3.0), 0.0)
    if k == 'cineon':
        bo = 10.0**((95.0-685.0)/300.0)
        q = r*(1.0-bo)+bo
        return -300.0*(1.0-bo)**2/(1023.0*LN10*q**2)
    raise ValueError(name)


def g1_stop(name, r):
    return LN2 * r * d1(name, r)


def g2_stop(name, r):
    return (LN2**2) * (r*d1(name, r) + (r**2)*d2(name, r))


def join_metrics(name):
    c = curves[name]
    k = c['kind']
    if not np.isfinite(c.get('join', np.nan)):
        return None
    j = float(c['join'])
    # Explicit one-sided formula evaluations to avoid np.where selecting only one branch.
    if k == 'commonlog':
        low_y = c['e']*j+c['f']
        high_y = c['c']*math.log10(c['a']*j+c['b'])+c['d']
        low_d1 = c['e']
        high_d1 = c['c']*c['a']/((c['a']*j+c['b'])*LN10)
        low_d2 = 0.0
        high_d2 = -c['c']*c['a']**2/(((c['a']*j+c['b'])**2)*LN10)
    elif k == 'logc4':
        low_y = (j-c['t'])/c['s']
        high_y = ((math.log2(c['a']*j+64.0)-6.0)/14.0)*c['b']+c['c']
        low_d1 = 1.0/c['s']
        high_d1 = c['b']*c['a']/(14.0*LN2*(c['a']*j+64.0))
        low_d2 = 0.0
        high_d2 = -c['b']*c['a']**2/(14.0*LN2*(c['a']*j+64.0)**2)
    elif k == 'slog3':
        low_y = (j*(171.2102946929-95.0)/0.01125+95.0)/1023.0
        high_y = (420.0+math.log10((j+0.01)/0.19)*261.5)/1023.0
        low_d1 = (171.2102946929-95.0)/(0.01125*1023.0)
        high_d1 = 261.5/(1023.0*LN10*(j+0.01))
        low_d2 = 0.0
        high_d2 = -261.5/(1023.0*LN10*(j+0.01)**2)
    elif k == 'vlog':
        low_y = 5.6*j+0.125
        high_y = 0.241514*math.log10(j+0.00873)+0.598206
        low_d1 = 5.6
        high_d1 = 0.241514/(LN10*(j+0.00873))
        low_d2 = 0.0
        high_d2 = -0.241514/(LN10*(j+0.00873)**2)
    elif k == 'nlog':
        low_y = 650.0*(j+0.0075)**(1.0/3.0)/1023.0
        high_y = (150.0*math.log(j)+619.0)/1023.0
        low_d1 = 650.0/(3.0*1023.0)*(j+0.0075)**(-2.0/3.0)
        high_d1 = 150.0/(1023.0*j)
        low_d2 = -1300.0/(9.0*1023.0)*(j+0.0075)**(-5.0/3.0)
        high_d2 = -150.0/(1023.0*j*j)
    elif k == 'canonlog':
        u = 0.0
        low_y = -0.45310179*math.log10(1.0-10.1596*u)+0.12512248
        high_y = 0.45310179*math.log10(1.0+10.1596*u)+0.12512248
        low_d1 = high_d1 = 0.45310179*10.1596/(LN10*0.9)
        fac = 1.0/(0.9**2)
        low_d2 = 0.45310179*10.1596**2/LN10*fac
        high_d2 = -low_d2
    elif k == 'canonlog2':
        u = 0.0
        low_y = -0.24136077*math.log10(1.0-87.099375*u)+0.092864125
        high_y = 0.24136077*math.log10(1.0+87.099375*u)+0.092864125
        low_d1 = high_d1 = 0.24136077*87.099375/(LN10*0.9)
        fac = 1.0/(0.9**2)
        low_d2 = 0.24136077*87.099375**2/LN10*fac
        high_d2 = -low_d2
    elif k == 'canonlog3':
        # Positive join on common r axis, published scene-linear u=0.014.
        u = 0.014
        low_y = 1.9754798*u+0.12512219
        high_y = 0.36726845*math.log10(14.98325*u+1.0)+0.12240537
        low_d1 = 1.9754798/0.9
        high_d1 = 0.36726845*14.98325/(LN10*(1.0+14.98325*u))/0.9
        low_d2 = 0.0
        high_d2 = -0.36726845*14.98325**2/(LN10*(1.0+14.98325*u)**2)/(0.9**2)
    elif k == 'log3g10':
        a,b,g = 0.224282,155.975327,15.1927
        z=0.0
        low_y = 0.0
        high_y = a*math.log10(z*b+1.0)
        low_d1 = g
        high_d1 = a*b/LN10
        low_d2 = 0.0
        high_d2 = -a*b*b/LN10
    elif k == 'lab':
        delta=6.0/29.0
        eps=delta**3
        low_f=(841.0/108.0)*eps+4.0/29.0
        high_f=eps**(1.0/3.0)
        low_y=(116.0*low_f-16.0)/100.0
        high_y=(116.0*high_f-16.0)/100.0
        low_d1=(116.0/100.0)*(841.0/108.0)
        high_d1=(116.0/100.0)*(1.0/3.0)*eps**(-2.0/3.0)
        low_d2=0.0
        high_d2=-(116.0/100.0)*(2.0/9.0)*eps**(-5.0/3.0)
    else:
        return None
    return {
        'join': j,
        'value_jump_high_minus_low': high_y-low_y,
        'slope_jump_high_minus_low': high_d1-low_d1,
        'second_derivative_jump_high_minus_low': high_d2-low_d2,
        'low_y': low_y, 'high_y': high_y,
        'low_d1': low_d1, 'high_d1': high_d1,
        'low_d2': low_d2, 'high_d2': high_d2,
    }


def continuity_label(vm, dm, tol_value=2e-4, tol_slope=5e-4):
    # Labels are intentionally conservative because many manufacturer coefficients are rounded.
    if abs(vm) <= 1e-10:
        c0 = 'yes (exact/as printed)'
    elif abs(vm) <= tol_value:
        c0 = 'approx. (within published precision)'
    else:
        c0 = 'no (as printed)'
    if abs(dm) <= 1e-10:
        c1 = 'yes (exact/as printed)'
    elif abs(dm) <= tol_slope:
        c1 = 'approx. (within published precision)'
    else:
        c1 = 'no (as printed)'
    return c0, c1


def make_plots():
    camera_names=[n for n,c in curves.items() if c['family']=='camera']
    ref_names=[n for n,c in curves.items() if c['family']=='reference']

    # dense x sampling including very low scene-linear values
    r=np.unique(np.r_[np.geomspace(1e-5, 0.02, 900), np.geomspace(0.02, 16.0, 1800)])
    stops=np.linspace(-12.0, 10.0, 1800)
    rs=0.18*(2.0**stops)

    plt.rcParams['svg.fonttype']='none'

    def legend(ax):
        ax.legend(frameon=False, fontsize=8, ncol=2)

    fig,ax=plt.subplots(figsize=(10,6.5))
    for n in camera_names:
        ax.plot(r,encode(n,r),label=n)
    ax.set_xscale('log'); ax.set_xlabel('Reflectance-like scene-linear input r (18% gray = 0.18)')
    ax.set_ylabel('Normalized encoded output'); ax.set_title('Published camera log curves — common reflectance-like axis')
    ax.grid(True,which='both',alpha=.25); legend(ax); fig.tight_layout()
    fig.savefig(OUTDIR/'camera_log_curves_scene_linear.svg'); fig.savefig(OUTDIR/'camera_log_curves_scene_linear.png',dpi=180); plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,6.5))
    for n in camera_names:
        ax.plot(r,d1(n,r),label=n)
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('r'); ax.set_ylabel("First derivative f'(r)"); ax.set_title('First derivative in scene-linear domain')
    ax.grid(True,which='both',alpha=.25); legend(ax); fig.tight_layout()
    fig.savefig(OUTDIR/'camera_log_first_derivative_scene_linear.svg'); fig.savefig(OUTDIR/'camera_log_first_derivative_scene_linear.png',dpi=180); plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,6.5))
    for n in camera_names:
        ax.plot(r,d2(n,r),label=n)
    ax.set_xscale('log'); ax.set_yscale('symlog',linthresh=1e-2)
    ax.set_xlabel('r'); ax.set_ylabel("Second derivative f''(r)"); ax.set_title('Second derivative in scene-linear domain (symlog y-scale)')
    ax.grid(True,which='both',alpha=.25); legend(ax); fig.tight_layout()
    fig.savefig(OUTDIR/'camera_log_second_derivative_scene_linear.svg'); fig.savefig(OUTDIR/'camera_log_second_derivative_scene_linear.png',dpi=180); plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,6.5))
    for n in camera_names:
        ax.plot(stops,encode(n,rs),label=n)
    ax.set_xlabel('Stops from 18% gray'); ax.set_ylabel('Normalized encoded output')
    ax.set_title('Published camera log curves — stop domain')
    ax.grid(True,alpha=.25); legend(ax); fig.tight_layout()
    fig.savefig(OUTDIR/'camera_log_curves_stops.svg'); fig.savefig(OUTDIR/'camera_log_curves_stops.png',dpi=180); plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,6.5))
    for n in camera_names:
        ax.plot(stops,g1_stop(n,rs),label=n)
    ax.set_xlabel('Stops from 18% gray'); ax.set_ylabel("g'(s): normalized output per stop")
    ax.set_title('Code allocation per stop')
    ax.grid(True,alpha=.25); legend(ax); fig.tight_layout()
    fig.savefig(OUTDIR/'camera_log_first_derivative_stops.svg'); fig.savefig(OUTDIR/'camera_log_first_derivative_stops.png',dpi=180); plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,6.5))
    for n in camera_names:
        ax.plot(stops,g2_stop(n,rs),label=n)
    ax.set_xlabel('Stops from 18% gray'); ax.set_ylabel("g''(s): change of allocation per stop²")
    ax.set_title('Second derivative in stop domain')
    ax.grid(True,alpha=.25); legend(ax); fig.tight_layout()
    fig.savefig(OUTDIR/'camera_log_second_derivative_stops.svg'); fig.savefig(OUTDIR/'camera_log_second_derivative_stops.png',dpi=180); plt.close(fig)

    # Reference curves, deliberately separate because Lab and Cineon do not have the same role as camera OETFs.
    rref=np.unique(np.r_[np.geomspace(1e-5,0.02,900),np.geomspace(0.02,1.5,1200)])
    fig,ax=plt.subplots(figsize=(9,5.8))
    for n in ref_names:
        ax.plot(rref,encode(n,rref),label=n)
    ax.set_xscale('log'); ax.set_xlabel('Normalized linear input'); ax.set_ylabel('Normalized output')
    ax.set_title('Reference functions: CIE L* and Cineon')
    ax.grid(True,which='both',alpha=.25); ax.legend(frameon=False); fig.tight_layout()
    fig.savefig(OUTDIR/'reference_curves_lab_cineon.svg'); fig.savefig(OUTDIR/'reference_curves_lab_cineon.png',dpi=180); plt.close(fig)

    # Lab junction detail: value and derivative as separate figures.
    eps=(6.0/29.0)**3
    rr=np.linspace(eps*0.35,eps*1.8,800)
    fig,ax=plt.subplots(figsize=(8,5))
    ax.plot(rr,encode('CIE L* / 100',rr))
    ax.axvline(eps,linestyle='--',linewidth=1)
    ax.set_xlabel('Y/Yn'); ax.set_ylabel('L*/100'); ax.set_title('CIE L*: value around the piecewise junction')
    ax.grid(True,alpha=.25); fig.tight_layout(); fig.savefig(OUTDIR/'lab_junction_value.svg'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5))
    ax.plot(rr,d1('CIE L* / 100',rr))
    ax.axvline(eps,linestyle='--',linewidth=1)
    ax.set_xlabel('Y/Yn'); ax.set_ylabel("d(L*/100)/d(Y/Yn)"); ax.set_title('CIE L*: matched first derivative at the junction')
    ax.grid(True,alpha=.25); fig.tight_layout(); fig.savefig(OUTDIR/'lab_junction_first_derivative.svg'); plt.close(fig)

    # Long sampled data table.
    data={'r_scene_linear':r}
    for n in camera_names:
        slug=''.join(ch.lower() if ch.isalnum() else '_' for ch in n).strip('_')
        data[f'{slug}__y']=encode(n,r)
        data[f'{slug}__dy_dr']=d1(n,r)
        data[f'{slug}__d2y_dr2']=d2(n,r)
    pd.DataFrame(data).to_csv(OUTDIR/'sampled_camera_curves.csv',index=False)

    data2={'stops_from_18pct':stops,'r_scene_linear':rs}
    for n in camera_names:
        slug=''.join(ch.lower() if ch.isalnum() else '_' for ch in n).strip('_')
        data2[f'{slug}__y']=encode(n,rs)
        data2[f'{slug}__dy_dstop']=g1_stop(n,rs)
        data2[f'{slug}__d2y_dstop2']=g2_stop(n,rs)
    pd.DataFrame(data2).to_csv(OUTDIR/'sampled_camera_curves_stops.csv',index=False)


def make_tables():
    camera_names=[n for n,c in curves.items() if c['family']=='camera']
    rows=[]
    for n in camera_names:
        y=float(encode(n,0.18))
        rows.append({
            'curve':n,
            'normalized_output_at_18pct':y,
            '1023x_output_reference':1023.0*y,
            'scene_linear_d1_at_18pct':float(d1(n,0.18)),
            'scene_linear_d2_at_18pct':float(d2(n,0.18)),
            'normalized_output_per_stop_at_18pct':float(g1_stop(n,0.18)),
            '1023x_output_per_stop_at_18pct':float(1023.0*g1_stop(n,0.18)),
            'stop_domain_d2_at_18pct':float(g2_stop(n,0.18)),
            'source_key':curves[n]['source_key'],
        })
    pd.DataFrame(rows).to_csv(OUTDIR/'summary_at_18pct.csv',index=False)

    jrows=[]
    for n,c in curves.items():
        jm=join_metrics(n)
        if jm is None:
            jrows.append({
                'curve':n,'role':c['family'],'join':np.nan,'join_domain':c['join_domain'],
                'low_branch':c['low_type'],'high_branch':c['high_type'],
                'C0_value':'smooth/no piecewise join','C1_slope':'smooth/no piecewise join','C2_curvature':'smooth/no piecewise join',
                'value_jump':np.nan,'slope_jump':np.nan,'second_derivative_jump':np.nan,
                'source_key':c['source_key']
            })
            continue
        c0,c1=continuity_label(jm['value_jump_high_minus_low'],jm['slope_jump_high_minus_low'])
        if abs(jm['second_derivative_jump_high_minus_low']) <= 1e-8:
            c2='yes (as printed)'
        else:
            c2='no'
        jrows.append({
            'curve':n,'role':c['family'],'join':jm['join'],'join_domain':c['join_domain'],
            'low_branch':c['low_type'],'high_branch':c['high_type'],
            'C0_value':c0,'C1_slope':c1,'C2_curvature':c2,
            'value_jump':jm['value_jump_high_minus_low'],
            'slope_jump':jm['slope_jump_high_minus_low'],
            'second_derivative_jump':jm['second_derivative_jump_high_minus_low'],
            'source_key':c['source_key']
        })
    pd.DataFrame(jrows).to_csv(OUTDIR/'junction_continuity.csv',index=False)


if __name__=='__main__':
    make_plots()
    make_tables()
    print('Generated extended log-gamma artifacts in', OUTDIR)
