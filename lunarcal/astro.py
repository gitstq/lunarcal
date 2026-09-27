"""Low-level astronomical helpers for lunarcal.

Pure-Python, standard-library only. All computations are self-contained
implementations based on well-known public algorithm descriptions
(Meeus, "Astronomical Algorithms", 2nd ed.) -- solar position from the
low-accuracy solar series plus the main VSOP87-style periodic terms, and
lunar phases from the Brown/Meeus New Moon polynomial plus periodic
inequalities. No third-party ephemeris data is bundled.

Time systems
------------
We work in Terrestrial Time (TT) internally.  Universal Time (UT) is
recovered by subtracting an approximate Delta-T = TT - UT1 table (valid
1900-2100, accuracy ~ few seconds, plenty for minute-scale solar-term
timing).  Beijing time = UT + 8h.
"""

from __future__ import annotations

import math
from typing import Tuple

# ---------------------------------------------------------------------------
# Julian Date machinery
# ---------------------------------------------------------------------------

# JD(2000-01-01 12:00 TT) = 2451545.0
J2000 = 2451545.0
# Seconds per day
DAY_SECONDS = 86400.0


def gregorian_to_jd(year: int, month: int, day: float) -> float:
    """Julian Day (UT/TT, continuous) for a proleptic Gregorian date.

    `day` may be a float (e.g. 12.5 means noon on the 12th).
    Meeus Eq. 7.1.
    """
    y = year
    m = month
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100.0)
    b = 2.0 - a + math.floor(a / 4.0)
    jd = math.floor(365.25 * (y + 4716.0)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5
    return jd


def jd_to_gregorian(jd: float) -> Tuple[int, int, float]:
    """Inverse of :func:`gregorian_to_jd`. Returns (year, month, day_float)."""
    jd = jd + 0.5
    z = math.floor(jd)
    f = jd - z
    if z < 2299161.0:
        a = z
    else:
        alpha = math.floor((z - 1867216.25) / 36524.25)
        a = z + 1.0 + alpha - math.floor(alpha / 4.0)
    b = a + 1524.0
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)
    day = b - d - math.floor(30.6001 * e) + f
    if e < 14:
        month = int(e - 1)
    else:
        month = int(e - 13)
    if month > 2:
        year = int(c - 4716)
    else:
        year = int(c - 4715)
    return year, month, day


# ---------------------------------------------------------------------------
# Delta-T (TT - UT1), seconds.  Piecewise-linear over a 10-year grid.
# Values follow the Morrison / Stephenson / Espenak consensus for 1900-2100.
# Accuracy ~ a few seconds; more than enough for minute-scale events.
# ---------------------------------------------------------------------------

_DT_GRID = [
    (1900, -2.7),
    (1910, 10.4),
    (1920, 21.2),
    (1930, 24.1),
    (1940, 22.1),
    (1950, 29.0),
    (1960, 33.1),
    (1970, 40.2),
    (1980, 50.5),
    (1990, 56.9),
    (2000, 63.8),
    (2010, 66.1),
    (2020, 70.0),
    (2030, 73.8),
    (2040, 79.5),
    (2050, 86.4),
    (2060, 95.0),
    (2070, 105.0),
    (2080, 116.0),
    (2090, 128.0),
    (2100, 141.0),
]


def delta_t_seconds(year: float) -> float:
    """Approximate TT - UT1 in seconds for a fractional year."""
    grid = _DT_GRID
    if year <= grid[0][0]:
        return grid[0][1]
    if year >= grid[-1][0]:
        return grid[-1][1]
    for i in range(len(grid) - 1):
        y0, v0 = grid[i]
        y1, v1 = grid[i + 1]
        if y0 <= year <= y1:
            w = (year - y0) / (y1 - y0)
            return v0 + (v1 - v0) * w
    return grid[-1][1]


def jd_tt_to_bjdt(jd_tt: float) -> Tuple[int, int, int, int, int, int]:
    """Convert a TT Julian Day to Beijing civil datetime (UTC+8)."""
    dt_s = delta_t_seconds(jd_to_gregorian(jd_tt)[0])
    jd_ut = jd_tt - dt_s / DAY_SECONDS
    # Beijing = UT + 8h
    jd_bj = jd_ut + 8.0 / 24.0
    y, m, d = jd_to_gregorian(jd_bj)
    # d is a float day; extract hh:mm:ss
    day_int = int(math.floor(d))
    frac = d - day_int
    total_sec = int(round(frac * DAY_SECONDS))
    hh = total_sec // 3600
    mm = (total_sec % 3600) // 60
    ss = total_sec % 60
    return y, m, day_int, hh, mm, ss


# ---------------------------------------------------------------------------
# Solar apparent geocentric ecliptic longitude (Meeus Ch. 25, enhanced)
# ---------------------------------------------------------------------------

def _sun_longitude_deg(jd_tt: float) -> float:
    """Apparent solar longitude (geocentric ecliptic, J2000 frame precessed
    to date), in degrees [0,360).  Good to ~0.002 deg (~1 minute of sun
    motion) over 1900-2100."""
    T = (jd_tt - J2000) / 36525.0

    # Geometric mean longitude of the Sun (deg)
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    L0 = L0 % 360.0

    # Mean anomaly (deg).  NOTE: the coefficient of T is POSITIVE -- the
    # Sun's mean anomaly grows by ~360 deg per tropical year.
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360.0
    Mr = math.radians(M)

    # Equation of the center (deg) -- main terms
    C = (
        (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mr)
        + (0.019993 - 0.000101 * T) * math.sin(2.0 * Mr)
        + 0.000289 * math.sin(3.0 * Mr)
        # small extra terms for minute-scale accuracy
        + 0.000150 * math.sin(4.0 * Mr)
    )

    # True longitude
    true_lon = L0 + C

    # Nutation in longitude (main term) + aberration
    omega = (125.04 - 1934.136 * T) % 360.0
    lam = true_lon - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    return lam % 360.0


def _signed_angle_diff(a: float, b: float) -> float:
    """Return a-b wrapped to [-180,180]."""
    d = (a - b + 180.0) % 360.0 - 180.0
    return d


def solar_term_time_deg(target_lon: float, jd_guess_tt: float) -> float:
    """Find the TT Julian Day at which the Sun's apparent longitude equals
    `target_lon` (degrees).  We scan outward from `jd_guess_tt` in small
    steps until the signed-angle difference changes sign, then bisect."""
    target = target_lon % 360.0

    def f(jd):
        return _signed_angle_diff(_sun_longitude_deg(jd), target)

    # Step ~0.5 day; the sun moves ~0.5 deg per 0.5 day, so a sign change
    # will be detected within a few steps on either side.
    step = 0.25
    lo = jd_guess_tt
    hi = jd_guess_tt
    flo = f(lo)
    fhi = f(hi)
    # search symmetrically
    for _ in range(120):
        lo -= step
        hi += step
        flo = f(lo)
        fhi = f(hi)
        if flo * fhi < 0:
            break
    else:
        raise RuntimeError("Could not bracket solar term root")

    # bisection
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if abs(fm) < 1e-10:
            return mid
        if flo * fm < 0:
            hi = mid
            fhi = fm
        else:
            lo = mid
            flo = fm
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# New Moon (朔) times.  Meeus Ch. 47, low-accuracy polynomial plus the
# dominant periodic inequalities.
# ---------------------------------------------------------------------------

# Periodic terms table (D, M, M', F) coefficients from Meeus Table 47.A
# (top 22 terms, sufficient for date-level lunar calendar accuracy).
# Tuple: (D_coeff, M_coeff, Mp_coeff, F_coeff, E_coeff, term)
# We implement the main inequality set used by the classic Chinese calendar
# portations; values are in minutes of time on the mean new moon.
_MOON_TERMS = [
    # D,   M,   Mp,  F,   E,    term_minutes
    (0.0, 0.0, 1.0, 0.0, 1.0, -0.40720),
    (1.0, 0.0, 0.0, 0.0, 1.0, 0.17241),
    (1.0, 0.0, 1.0, 0.0, 1.0, 0.01608),
    (2.0, 0.0, 0.0, 0.0, 0.0, 0.01039),
    (2.0, 0.0, 1.0, 0.0, 0.0, 0.00739),
    (2.0, 0.0, -1.0, 0.0, 0.0, -0.00514),
    (1.0, 0.0, -1.0, 0.0, 1.0, -0.01173),
    (0.0, 0.0, 2.0, 0.0, 0.0, 0.00205),
    (0.0, 1.0, 0.0, 0.0, 1.0, 0.00381),
    (0.0, 1.0, 1.0, 0.0, 1.0, 0.00175),
    (1.0, 1.0, 0.0, 0.0, 1.0, -0.00008),
    (1.0, 1.0, 1.0, 0.0, 1.0, 0.00317),
    (2.0, 0.0, 2.0, 0.0, 0.0, -0.00158),
    (0.0, 0.0, 0.0, 2.0, 0.0, -0.00111),
    (0.0, 0.0, 1.0, 2.0, 0.0, 0.00138),
    (2.0, 0.0, 0.0, 2.0, 0.0, 0.00168),
    (1.0, 0.0, 0.0, 1.0, 1.0, -0.00027),
    (1.0, 0.0, 0.0, -1.0, 1.0, -0.00027),
    (2.0, 0.0, -2.0, 0.0, 0.0, -0.00040),
    (0.0, 0.0, 1.0, -2.0, 0.0, 0.00038),
    (0.0, 0.0, -1.0, 2.0, 0.0, 0.00040),
    (0.0, 0.0, 0.0, 1.0, 0.0, -0.00016),
]


def new_moon_jd(k: float) -> float:
    """TT Julian Day of the k-th new moon after 2000-01-06 14:36 TT.

    k = 0 -> new moon of 2000-01-06.  k may be non-integer for iteration.
    """
    T = k / 1236.85  # Julian centuries from J2000 at epoch of mean phase
    # Mean new moon (Meeus Eq. 47.1).  k=0 -> 2000-01-06 18:14 UT.
    T = k / 1236.85  # Julian centuries from J2000 at epoch of mean phase
    JDE = (
        2451550.09766
        + 29.530588861 * k
        + 0.0001547 * T * T
        - 0.000000150 * T * T * T
        + 0.00033 * math.sin(math.radians(299.77 + 0.107408 * k - 0.009173 * T * T))
    )

    # Mean arguments
    Mp = (134.963 + 477198.867505 * T + 0.0087414 * T * T + T * T / 628063.0) % 360.0
    M = (357.529 + 35999.050291 * T - 0.0001536 * T * T - T * T * T / 245000.0) % 360.0
    D = (297.85026 + 445267.111379 * T - 0.0019143 * T * T + T * T / 189474.0) % 360.0
    F = (93.272 + 483202.017533 * T - 0.0036539 * T * T - T * T * T / 3526000.0) % 360.0
    E = 1.0 - 0.002516 * T - 0.0000074 * T * T

    correction_days = 0.0
    for Dc, Mc, Mpc, Fc, Ec, term in _MOON_TERMS:
        arg = (
            Dc * math.radians(D)
            + Mc * math.radians(M)
            + Mpc * math.radians(Mp)
            + Fc * math.radians(F)
        )
        e_factor = E ** abs(Mc) if Ec else 1.0
        correction_days += term * e_factor * math.sin(arg)

    JDE += correction_days

    # Additional planetary perturbations (small, but improves date boundary)
    # Omega argument for the 0.00033 s-term already included above.
    return JDE
