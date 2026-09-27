"""Curve registry + analytic derivatives for published transfer-function implementations.

The human-editable curve list lives in curve_specs/curves.yaml.  Most future additions
only require a registry entry.  If a new mathematical family is encountered, add one
model branch to encode/d1/d2 here; all tables, SVGs, HTML, CSVs and the static PDF are
then rebuilt by scripts/build_all.py.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

LN2 = math.log(2.0)
LN10 = math.log(10.0)


def load_registry(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    curves_doc = yaml.safe_load((root / "curve_specs" / "curves.yaml").read_text(encoding="utf-8"))
    sources_doc = yaml.safe_load((root / "curve_specs" / "sources.yaml").read_text(encoding="utf-8"))
    curves = [resolve_curve(c) for c in curves_doc["curves"]]
    config = curves_doc.get("comparison", {})
    return {"curves": curves, "comparison": config}, sources_doc["sources"]


def resolve_curve(curve: dict[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(curve)
    p = c.setdefault("params", {})
    model = c["model"]
    if model == "logc4":
        code_max = float(p["code_max"])
        black_code = float(p["black_code"])
        exposure_scale = float(p["exposure_scale"])
        b = (code_max - black_code) / code_max
        cc = black_code / code_max
        a = (2.0**18 - 16.0) / exposure_scale
        s = 14.0 * LN2 * 2.0 ** (6.0 - 14.0 * cc / b) / (a * b)
        t = (2.0 ** (6.0 - 14.0 * cc / b) - 64.0) / a
        p.update({"a": a, "b": b, "c": cc, "s": s, "t": t})
    for j in c.get("junctions", []):
        if "value" in j:
            continue
        derived = j.get("derived")
        if derived == "logc4_t":
            j["value"] = p["t"]
        elif derived == "canonlog3_positive":
            j["value"] = float(p["reflection_scale"]) * float(p["published_join"])
        elif derived == "canonlog3_negative":
            j["value"] = -float(p["reflection_scale"]) * float(p["published_join"])
        elif derived == "lab_epsilon":
            j["value"] = (6.0 / 29.0) ** 3
        else:
            raise ValueError(f"Unknown derived junction: {derived} for {c['name']}")
    return c


def curve_by_id(registry: dict[str, Any], curve_id: str) -> dict[str, Any]:
    for c in registry["curves"]:
        if c["id"] == curve_id:
            return c
    raise KeyError(curve_id)


def _arr(x):
    return np.asarray(x, dtype=float)


def encode(c: dict[str, Any], r):
    r = _arr(r)
    p = c["params"]
    k = c["model"]
    if k == "commonlog":
        return np.where(r >= p["cut"], p["c"] * np.log10(p["a"] * r + p["b"]) + p["d"], p["e"] * r + p["f"])
    if k == "logc4":
        return np.where(r >= p["t"], ((np.log2(p["a"] * r + 64.0) - 6.0) / 14.0) * p["b"] + p["c"], (r - p["t"]) / p["s"])
    if k == "slog3":
        cut = p["cut"]
        return np.where(r >= cut, (420.0 + np.log10((r + 0.01) / (0.18 + 0.01)) * 261.5) / 1023.0,
                        (r * (171.2102946929 - 95.0) / cut + 95.0) / 1023.0)
    if k == "vlog":
        cut = p["cut"]
        return np.where(r >= cut, 0.241514 * np.log10(r + 0.00873) + 0.598206, 5.6 * r + 0.125)
    if k == "nlog":
        cut = p["cut"]
        out = np.empty_like(r)
        m = r < cut
        out[m] = 650.0 * np.cbrt(r[m] + 0.0075) / 1023.0
        out[~m] = (150.0 * np.log(r[~m]) + 619.0) / 1023.0
        return out
    if k == "canonlog":
        u = r / p["reflection_scale"]
        out = np.empty_like(u)
        m = u < 0.0
        out[m] = -0.45310179 * np.log10(1.0 - 10.1596 * u[m]) + 0.12512248
        out[~m] = 0.45310179 * np.log10(10.1596 * u[~m] + 1.0) + 0.12512248
        return out
    if k == "canonlog2":
        u = r / p["reflection_scale"]
        out = np.empty_like(u)
        m = u < 0.0
        out[m] = -0.24136077 * np.log10(1.0 - 87.099375 * u[m]) + 0.092864125
        out[~m] = 0.24136077 * np.log10(87.099375 * u[~m] + 1.0) + 0.092864125
        return out
    if k == "canonlog3":
        scale = p["reflection_scale"]
        j = p["published_join"]
        u = r / scale
        out = np.empty_like(u)
        m1 = u < -j
        m2 = (u >= -j) & (u <= j)
        m3 = u > j
        out[m1] = -0.36726845 * np.log10(1.0 - 14.98325 * u[m1]) + 0.12783901
        out[m2] = 1.9754798 * u[m2] + 0.12512219
        out[m3] = 0.36726845 * np.log10(14.98325 * u[m3] + 1.0) + 0.12240537
        return out
    if k == "log3g10":
        z = r + p["offset"]
        out = np.empty_like(r)
        m = z < 0.0
        out[m] = z[m] * p["linear_slope"]
        out[~m] = p["a"] * np.log10(z[~m] * p["b"] + 1.0)
        return out
    if k == "applelog":
        R0, Rt = p["R0"], p["Rt"]
        out = np.empty_like(r)
        m0 = r < R0
        m1 = (r >= R0) & (r < Rt)
        m2 = r >= Rt
        out[m0] = 0.0
        out[m1] = p["c"] * (r[m1] - R0) ** 2
        out[m2] = p["gamma"] * np.log2(r[m2] + p["beta"]) + p["delta"]
        return out
    if k == "djidlog":
        cut = p["cut"]
        return np.where(r <= cut, p["linear_slope"] * r + p["linear_offset"],
                        np.log10(r * p["log_input_scale"] + p["log_input_offset"]) * p["log_scale"] + p["log_offset"])
    if k == "lab":
        delta = 6.0 / 29.0
        eps = delta**3
        ff = np.where(r > eps, np.cbrt(r), (841.0 / 108.0) * r + 4.0 / 29.0)
        return (116.0 * ff - 16.0) / 100.0
    if k == "cineon":
        bo = 10.0 ** ((p["black_code"] - p["white_code"]) / p["density_codes_per_decade"])
        q = r * (1.0 - bo) + bo
        return (p["white_code"] + p["density_codes_per_decade"] * np.log10(q)) / p["code_max"]
    raise ValueError(f"Unknown model: {k}")


def d1(c: dict[str, Any], r):
    r = _arr(r)
    p = c["params"]
    k = c["model"]
    if k == "commonlog":
        return np.where(r >= p["cut"], p["c"] * p["a"] / ((p["a"] * r + p["b"]) * LN10), p["e"])
    if k == "logc4":
        return np.where(r >= p["t"], p["b"] * p["a"] / (14.0 * LN2 * (p["a"] * r + 64.0)), 1.0 / p["s"])
    if k == "slog3":
        cut = p["cut"]
        slope = (171.2102946929 - 95.0) / (cut * 1023.0)
        return np.where(r >= cut, 261.5 / (1023.0 * LN10 * (r + 0.01)), slope)
    if k == "vlog":
        return np.where(r >= p["cut"], 0.241514 / (LN10 * (r + 0.00873)), 5.6)
    if k == "nlog":
        cut = p["cut"]
        out = np.empty_like(r)
        m = r < cut
        out[m] = 650.0 / (3.0 * 1023.0) * (r[m] + 0.0075) ** (-2.0 / 3.0)
        out[~m] = 150.0 / (1023.0 * r[~m])
        return out
    if k == "canonlog":
        scale = p["reflection_scale"]
        u = r / scale
        return np.where(u < 0.0,
                        0.45310179 * 10.1596 / (LN10 * (1.0 - 10.1596 * u)) / scale,
                        0.45310179 * 10.1596 / (LN10 * (1.0 + 10.1596 * u)) / scale)
    if k == "canonlog2":
        scale = p["reflection_scale"]
        u = r / scale
        return np.where(u < 0.0,
                        0.24136077 * 87.099375 / (LN10 * (1.0 - 87.099375 * u)) / scale,
                        0.24136077 * 87.099375 / (LN10 * (1.0 + 87.099375 * u)) / scale)
    if k == "canonlog3":
        scale = p["reflection_scale"]
        j = p["published_join"]
        u = r / scale
        out = np.empty_like(u)
        m1 = u < -j
        m2 = (u >= -j) & (u <= j)
        m3 = u > j
        out[m1] = 0.36726845 * 14.98325 / (LN10 * (1.0 - 14.98325 * u[m1])) / scale
        out[m2] = 1.9754798 / scale
        out[m3] = 0.36726845 * 14.98325 / (LN10 * (1.0 + 14.98325 * u[m3])) / scale
        return out
    if k == "log3g10":
        z = r + p["offset"]
        out = np.empty_like(r)
        m = z < 0.0
        out[m] = p["linear_slope"]
        out[~m] = p["a"] * p["b"] / (LN10 * (z[~m] * p["b"] + 1.0))
        return out
    if k == "applelog":
        R0, Rt = p["R0"], p["Rt"]
        out = np.empty_like(r)
        m0 = r < R0
        m1 = (r >= R0) & (r < Rt)
        m2 = r >= Rt
        out[m0] = 0.0
        out[m1] = 2.0 * p["c"] * (r[m1] - R0)
        out[m2] = p["gamma"] / (LN2 * (r[m2] + p["beta"]))
        return out
    if k == "djidlog":
        cut = p["cut"]
        return np.where(r <= cut, p["linear_slope"],
                        p["log_scale"] * p["log_input_scale"] / (LN10 * (r * p["log_input_scale"] + p["log_input_offset"])))
    if k == "lab":
        delta = 6.0 / 29.0
        eps = delta**3
        return np.where(r > eps, (116.0 / 100.0) * (1.0 / 3.0) * r ** (-2.0 / 3.0), (116.0 / 100.0) * (841.0 / 108.0))
    if k == "cineon":
        bo = 10.0 ** ((p["black_code"] - p["white_code"]) / p["density_codes_per_decade"])
        q = r * (1.0 - bo) + bo
        return p["density_codes_per_decade"] * (1.0 - bo) / (p["code_max"] * LN10 * q)
    raise ValueError(f"Unknown model: {k}")


def d2(c: dict[str, Any], r):
    r = _arr(r)
    p = c["params"]
    k = c["model"]
    if k == "commonlog":
        return np.where(r >= p["cut"], -p["c"] * p["a"] ** 2 / (((p["a"] * r + p["b"]) ** 2) * LN10), 0.0)
    if k == "logc4":
        return np.where(r >= p["t"], -p["b"] * p["a"] ** 2 / (14.0 * LN2 * (p["a"] * r + 64.0) ** 2), 0.0)
    if k == "slog3":
        return np.where(r >= p["cut"], -261.5 / (1023.0 * LN10 * (r + 0.01) ** 2), 0.0)
    if k == "vlog":
        return np.where(r >= p["cut"], -0.241514 / (LN10 * (r + 0.00873) ** 2), 0.0)
    if k == "nlog":
        cut = p["cut"]
        out = np.empty_like(r)
        m = r < cut
        out[m] = -1300.0 / (9.0 * 1023.0) * (r[m] + 0.0075) ** (-5.0 / 3.0)
        out[~m] = -150.0 / (1023.0 * r[~m] ** 2)
        return out
    if k == "canonlog":
        scale = p["reflection_scale"]
        u = r / scale
        fac = 1.0 / scale**2
        return np.where(u < 0.0,
                        0.45310179 * 10.1596**2 / (LN10 * (1.0 - 10.1596 * u) ** 2) * fac,
                        -0.45310179 * 10.1596**2 / (LN10 * (1.0 + 10.1596 * u) ** 2) * fac)
    if k == "canonlog2":
        scale = p["reflection_scale"]
        u = r / scale
        fac = 1.0 / scale**2
        return np.where(u < 0.0,
                        0.24136077 * 87.099375**2 / (LN10 * (1.0 - 87.099375 * u) ** 2) * fac,
                        -0.24136077 * 87.099375**2 / (LN10 * (1.0 + 87.099375 * u) ** 2) * fac)
    if k == "canonlog3":
        scale = p["reflection_scale"]
        j = p["published_join"]
        u = r / scale
        out = np.empty_like(u)
        m1 = u < -j
        m2 = (u >= -j) & (u <= j)
        m3 = u > j
        fac = 1.0 / scale**2
        out[m1] = 0.36726845 * 14.98325**2 / (LN10 * (1.0 - 14.98325 * u[m1]) ** 2) * fac
        out[m2] = 0.0
        out[m3] = -0.36726845 * 14.98325**2 / (LN10 * (1.0 + 14.98325 * u[m3]) ** 2) * fac
        return out
    if k == "log3g10":
        z = r + p["offset"]
        out = np.empty_like(r)
        m = z < 0.0
        out[m] = 0.0
        out[~m] = -p["a"] * p["b"]**2 / (LN10 * (z[~m] * p["b"] + 1.0) ** 2)
        return out
    if k == "applelog":
        R0, Rt = p["R0"], p["Rt"]
        out = np.empty_like(r)
        m0 = r < R0
        m1 = (r >= R0) & (r < Rt)
        m2 = r >= Rt
        out[m0] = 0.0
        out[m1] = 2.0 * p["c"]
        out[m2] = -p["gamma"] / (LN2 * (r[m2] + p["beta"]) ** 2)
        return out
    if k == "djidlog":
        cut = p["cut"]
        return np.where(r <= cut, 0.0,
                        -p["log_scale"] * p["log_input_scale"]**2 / (LN10 * (r * p["log_input_scale"] + p["log_input_offset"]) ** 2))
    if k == "lab":
        delta = 6.0 / 29.0
        eps = delta**3
        return np.where(r > eps, -(116.0 / 100.0) * (2.0 / 9.0) * r ** (-5.0 / 3.0), 0.0)
    if k == "cineon":
        bo = 10.0 ** ((p["black_code"] - p["white_code"]) / p["density_codes_per_decade"])
        q = r * (1.0 - bo) + bo
        return -p["density_codes_per_decade"] * (1.0 - bo) ** 2 / (p["code_max"] * LN10 * q**2)
    raise ValueError(f"Unknown model: {k}")


def g1_stop(c: dict[str, Any], r):
    r = _arr(r)
    return LN2 * r * d1(c, r)


def g2_stop(c: dict[str, Any], r):
    r = _arr(r)
    return LN2**2 * (r * d1(c, r) + r**2 * d2(c, r))


def primary_junction(c: dict[str, Any]) -> dict[str, Any] | None:
    js = c.get("junctions", [])
    if not js:
        return None
    for j in js:
        if j.get("primary"):
            return j
    return js[0]


def junction_metrics(c: dict[str, Any], j: dict[str, Any]) -> dict[str, float]:
    x = float(j["value"])
    left = np.nextafter(x, -np.inf)
    right = np.nextafter(x, np.inf)
    ly, ry = float(encode(c, left)), float(encode(c, right))
    ld1, rd1 = float(d1(c, left)), float(d1(c, right))
    ld2, rd2 = float(d2(c, left)), float(d2(c, right))
    return {
        "join": x,
        "low_y": ly, "high_y": ry,
        "low_d1": ld1, "high_d1": rd1,
        "low_d2": ld2, "high_d2": rd2,
        "value_jump_high_minus_low": ry - ly,
        "slope_jump_high_minus_low": rd1 - ld1,
        "second_derivative_jump_high_minus_low": rd2 - ld2,
    }


def continuity_label(value_jump: float, slope_jump: float, second_jump: float,
                     tol_value: float = 2e-4, tol_slope: float = 5e-4, tol_second: float = 1e-8):
    def label(v, tol):
        if abs(v) <= 1e-10:
            return "yes (exact/as printed)"
        if abs(v) <= tol:
            return "approx. (within published precision)"
        return "no (as printed)"
    c0 = label(value_jump, tol_value)
    c1 = label(slope_jump, tol_slope)
    c2 = "yes (exact/as printed)" if abs(second_jump) <= tol_second else "no"
    return c0, c1, c2
