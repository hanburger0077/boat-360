import os
import cv2


camera_names = ["front", "back", "left", "right"]

# --------------------------------------------------------------------
# Convention: 1 bird-view pixel == 1 cm on the ground (unless you rescale).
#
# Outer calibration frame (pattern only, excluding shift bands):
#   6.1 m along vehicle left-right  -> image x
#   5.1 m along vehicle front-back -> image y (top of image = front)
# Inner void (car overlay), centered in pattern:
#   3.1 m x 2.1 m  (left-right x front-back)
#
# shift_w / shift_h: extra ground visible OUTSIDE the cloth on each side.
#   Requested: 0.7 m per side  =>  70 px (cm) each.
# --------------------------------------------------------------------
PATTERN_W = 610   # 6.1 m
PATTERN_H = 510   # 5.1 m
CAR_W = 310       # 3.1 m (left-right)
CAR_H = 210       # 2.1 m (front-back)

shift_w = 70      # 0.7 m beyond cloth, left & right
shift_h = 70      # 0.7 m beyond cloth, front & back

# Fine nudge of car rectangle inside pattern (cm); (0, 0) = geometric center
inn_shift_w = 0
inn_shift_h = 0

total_w = PATTERN_W + 2 * shift_w
total_h = PATTERN_H + 2 * shift_h

xl = shift_w + (PATTERN_W - CAR_W) // 2 + inn_shift_w
xr = total_w - xl
yt = shift_h + (PATTERN_H - CAR_H) // 2 + inn_shift_h
yb = total_h - yt
# --------------------------------------------------------------------

project_shapes = {
    "front": (total_w, yt),
    "back":  (total_w, yt),
    "left":  (total_h, xl),
    "right": (total_h, xl)
}

# Homography dst rectangle placement (legacy / centered-strip).
# Size: 140 x 100 px => 1.4 m x 1.0 m on ground.
#
# For each camera, click the matching 1.4m x 1.0m rectangle corners on the
# undistorted image in the same order:
#   left-top -> right-top -> left-bottom -> right-bottom
#
# For side cameras, the dst coordinate system is swapped (x=global_y, y=global_x),
# consistent with the original repo's param_settings.py.
_KP_W = 140
_KP_H = 100

_LEGACY_CX = shift_w + PATTERN_W // 2
_LEGACY_TOP = shift_h
_LEGACY_SIDE_C = shift_h + PATTERN_H // 2

project_keypoints = {
    "front": [(_LEGACY_CX - _KP_W // 2, _LEGACY_TOP),
              (_LEGACY_CX + _KP_W // 2, _LEGACY_TOP),
              (_LEGACY_CX - _KP_W // 2, _LEGACY_TOP + _KP_H),
              (_LEGACY_CX + _KP_W // 2, _LEGACY_TOP + _KP_H)],

    "back":  [(_LEGACY_CX - _KP_W // 2, _LEGACY_TOP),
              (_LEGACY_CX + _KP_W // 2, _LEGACY_TOP),
              (_LEGACY_CX - _KP_W // 2, _LEGACY_TOP + _KP_H),
              (_LEGACY_CX + _KP_W // 2, _LEGACY_TOP + _KP_H)],

    # side cameras use swapped dst axes: (global_y, global_x)
    "left":  [(_LEGACY_SIDE_C - _KP_W // 2, shift_w),
              (_LEGACY_SIDE_C + _KP_W // 2, shift_w),
              (_LEGACY_SIDE_C - _KP_W // 2, shift_w + _KP_H),
              (_LEGACY_SIDE_C + _KP_W // 2, shift_w + _KP_H)],

    "right": [(_LEGACY_SIDE_C - _KP_W // 2, shift_w),
              (_LEGACY_SIDE_C + _KP_W // 2, shift_w),
              (_LEGACY_SIDE_C - _KP_W // 2, shift_w + _KP_H),
              (_LEGACY_SIDE_C + _KP_W // 2, shift_w + _KP_H)]
}

car_image = cv2.imread(os.path.join(os.getcwd(), "images", "car.png"))
car_image = cv2.resize(car_image, (xr - xl, yb - yt))
