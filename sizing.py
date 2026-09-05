"""Proportional sizing for Charger Link.

All layout dimensions are anchored to the PHONE reference screenshot
(392x696) and scaled by window width, so the app renders correctly at
any window size (560x880 desktop default, 392x696 phone reference, ...).

Reference measurements (phone px, at @2.25x density => dp = px/2.25):
  titlebar red band            0..80      (common_titlebar top band)
  memory/profile spinner row  80..148    (common_titlebar 47dip row)
  icon grid: 3 rows x 3 cols   85-86px circles, 20px padding, 30px row gaps
  channel bar (bottom)        628..695   (common_channelbar 60dip + divider)
  Start/Stop buttons          45dp  (APK charge.xml)
  function grid icons         90dp  (APK main.xml)
"""
from __future__ import annotations

# reference canvas the phone screenshots were measured on
PH_REF_W = 392
PH_REF_H = 696


def scale(px: float, w: int) -> int:
    """Scale phone-reference pixels to window width `w`."""
    return int(px * (w / PH_REF_W))


# ---- phone-reference geometry (px) -----------------------------------------
TITLEBAR_H    = 78      # red band (measured 0..80 incl shadow)
TITLE_SIZE    = 24      # title px (measured)
SUBTITLE_SIZE = 12      # subtitle px
SPINNER_ROW_H = 60      # memory/profile row 80..148 in ref
BACK_MARGIN   = 8
BACK_BTN      = 46      # 40dp back button + margin

GRID_MARGIN    = 22     # ~20dip padding around the icon grid
GRID_HGAP     = 28      # horizontal gap between columns
GRID_VGAP     = 30      # 30dip spacer rows between icon rows
ICON_PX        = 86     # measured circle diameter
LABEL_PX       = 18     # label height under circle
LABEL_SIZE     = 10     # label text dp

CHBAR_H        = 68     # 60dip button row + 1dip divider
CHINFO_D       = 56     # right circular button (~40dip rendered w/ margin)
CHBTN_H        = 60

ACTION_BTN     = 106    # 45dp start/stop measured
ACTION_GAP     = 40
