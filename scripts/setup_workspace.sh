#!/usr/bin/env bash
# Sets up the Caddy AI2 workspace with the ZED 2i cameras.
#
#   scripts/setup_workspace.sh [TARGET_DIR] [PROFILE]
#
#   TARGET_DIR  default ~/caddy_ws
#   PROFILE     sim     (default) full simulation workspace, every package as a git submodule
#               jetson  only this package (real hardware); the container with the ZED SDK is separate
#
# Environment:
#   USE_HTTPS=1   rewrite the git@github.com: submodule URLs to https (machines without an SSH key)
#   SIM_BRANCH    branch of caddy_ai2_ros2_sim to clone (default feat/zed-2i-cameras)
set -euo pipefail

TARGET="${1:-$HOME/caddy_ws}"
PROFILE="${2:-sim}"
SIM_BRANCH="${SIM_BRANCH:-feat/zed-2i-cameras}"
OWNER_URL="https://github.com/racarla96"

if [[ "${USE_HTTPS:-0}" == "1" ]]; then
  git config --global url."https://github.com/".insteadOf "git@github.com:"
  echo "[setup] submodule URLs rewritten to https (global git config)"
fi

if [[ -e "$TARGET" && -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
  echo "[setup] $TARGET exists and is not empty, refusing to touch it" >&2
  exit 1
fi

case "$PROFILE" in
  sim)
    git clone --recurse-submodules -b "$SIM_BRANCH" "$OWNER_URL/caddy_ai2_ros2_sim.git" "$TARGET"
    cat <<EOF

[setup] Workspace cloned in $TARGET (branch $SIM_BRANCH).
Next, on a machine with ROS 2 Jazzy + Gazebo Harmonic (see README of caddy_ai2_ros2_sim):

  python3 -I $TARGET/src/caddy_ai2_ros2_camera_zed_2i/tools/check_render.py $TARGET/src   # no ROS needed
  cd $TARGET && colcon build --symlink-install --packages-select \\
      caddy_ai2_ros2_description caddy_ai2_ros2_gazebo_simulation caddy_ai2_ros2_camera_zed_2i \\
      caddy_ai2_ros2_sensors_rs_helios_5515 caddy_ai2_ros2_sim   # plus the rest listed in the README
  source install/setup.bash && ros2 launch caddy_ai2_ros2_sim sim.launch.py

Do NOT run 'git submodule update --remote': it moves description and gazebo_simulation to the tip
of 'jazzy' and drops the camera changes until the feat/zed-2i-cameras branches are merged.
EOF
    ;;
  jetson)
    mkdir -p "$TARGET/src"
    git clone "$OWNER_URL/caddy_ai2_ros2_camera_zed_2i.git" "$TARGET/src/caddy_ai2_ros2_camera_zed_2i"
    cat <<EOF

[setup] Only the camera package was cloned in $TARGET/src.
It still needs, inside the Jetson container (JetPack 6.2, ROS 2 Jazzy):
  - the ZED SDK and zed-ros2-wrapper (package zed_wrapper)  -> NOT provided here yet
  - the robot description (caddy_ai2_ros2_description) if this container publishes TF
See docs/HANDOFF.md, section "Pending: Jetson container".
EOF
    ;;
  *)
    echo "[setup] unknown PROFILE '$PROFILE' (use sim or jetson)" >&2
    exit 2
    ;;
esac
