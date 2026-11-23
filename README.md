# caddy_ai2_ros2_camera_zed_2i

Cámara estéreo **Stereolabs ZED 2i** para el Caddy AI2, siguiendo la estructura de
`caddy_ai2_ros2_sensors_rs_helios_5515`. Un único paquete que se instancia varias veces
(una entrada por cámara en `robot_params.yaml`).

**Licencia:** [CC BY 4.0](LICENSE.MD)

**Arrancar la cámara en la ZED Box:** [Quickstart (HTML)](docs/QUICKSTART.html) · [Quickstart (PDF)](docs/QUICKSTART.pdf). Incluye `docs/zed_view.rviz` para verla en RViz.
`zed_2i.launch.py` ya usa `publish_urdf:=true` (con `false` el nodo se bloqueaba esperando transformaciones); probado el 23-nov-2026 en la ZED Box.

## Estado

| Parte | Estado |
|---|---|
| Simulación (Gazebo Harmonic `rgbd_camera` → imagen, profundidad, nube de puntos) | ✅ escrita, **sin probar todavía en Gazebo** |
| Launch del hardware real (envuelve `zed-ros2-wrapper`) | ✅ escrito, **sin probar en la ZED Box** |
| ZED SDK en la ZED Box | ✅ **5.5.1 instalado nativo** (Ubuntu 24.04, L4T R39, CUDA 13.2); cámara aún sin abrir |
| Contenedor Docker | ❌ descartado: la ZED Box va con Ubuntu 24.04 y Jazzy nativos |
| Malla oficial de la cámara | ⏳ pendiente (caja provisional) |

> Para continuar el trabajo en otra sesión: [`docs/HANDOFF.md`](docs/HANDOFF.md). Instalación: `scripts/setup_workspace.sh`.

## Contenido

```
description/sensor.urdf.j2          # link + joint + frame óptico + sensor rgbd_camera (Jinja2)
bringup/config/sensor_params.yaml   # parámetros operativos (hardware real) y de simulación
bringup/launch/zed_2i.launch.py     # hardware real: zed_wrapper con camera_name y serial_number
tools/check_render.py               # comprobación sin ROS ni Gazebo de plantillas y bridge
scripts/setup_workspace.sh          # monta el workspace (sim) o solo este paquete (jetson)
docs/HANDOFF.md                     # estado, decisiones y pendientes
```

## Topics

Mismos nombres que el wrapper (`/<camera_name>/zed_node/...`), con `camera_name` = clave del
sensor en `robot_params.yaml`:

```
/<camera_name>/zed_node/left/color/rect/image          sensor_msgs/msg/Image
/<camera_name>/zed_node/left/color/rect/camera_info    sensor_msgs/msg/CameraInfo
/<camera_name>/zed_node/depth/depth_registered         sensor_msgs/msg/Image
/<camera_name>/zed_node/point_cloud/cloud_registered   sensor_msgs/msg/PointCloud2
frame_id: <frame_id>_optical
```

En simulación la cámara es una sola `rgbd_camera` situada entre las dos lentes (no se simula
la base de 12 cm ni el IMU). Revisa los nombres contra la versión del wrapper que uses.

## Disposición de las dos cámaras (estudio)

Las dos disposiciones están definidas en `caddy_ai2_ros2_description/bringup/config/robot_params.yaml`.
**Solo una a la vez**: se activa con `enabled: true` en sus dos cámaras y `false` en las otras dos.

| | A. Dos delanteras (extremos, hacia fuera) | B. Una delante y una detrás (centradas) |
|---|---|---|
| Claves | `zed_2i_left`, `zed_2i_right` | `zed_2i_front`, `zed_2i_rear` |
| Yaw | ±40° (hacia fuera) | 0° y 180° |
| Cobertura horizontal | 190° delante, solape central de 30° | 2 × 110° = 220°, sin solape |
| Zonas ciegas | 170° detrás | 2 × 70° en los laterales |

Con FOV horizontal `H` y yaw `±θ` hacia fuera: solape `H − 2θ`, cobertura total `H + 2θ`.
Con el objetivo de 4 mm (`H = 72°`) cambia `horizontal_fov` en `sensor_params.yaml`.

Las poses están **provisionales**: hay que medirlas en la barra superior del vehículo.

## Hardware real

Requiere el ZED SDK y `zed_wrapper`, instalados **de forma nativa en la ZED Box** (no hay contenedor), y no se compilan en el workspace de simulación.

- **Wrapper fijado a `v5.5.0`** (`third_party/zed-ros2-wrapper`, commit `431dcf4`), que corresponde al ZED SDK **5.5.x**. El `master` del fork es `5.6.0-dev` y no se usa. No ejecutes `git submodule update --remote` sobre este submódulo: lo movería de vuelta al desarrollo.
- Dependencias de ROS (apt, Jazzy): `ros-jazzy-zed-msgs`, `zed-description`, `robot-localization`, `nmea-msgs`, `geographic-msgs`, `diagnostic-updater`, `image-transport-plugins`, `backward-ros`, `xacro`, y `nlohmann-json3-dev`.
- Las calibraciones de cada cámara se descargan la primera vez que se abre (necesita internet) en `/usr/local/zed/settings`.
- Número de serie: `lsusb` y `/sys/bus/usb/devices/*/serial` muestran el de la interfaz HID (p. ej. `32698440`).

```bash
ros2 launch caddy_ai2_ros2_camera_zed_2i zed_2i.launch.py camera_name:=zed_2i_left  serial_number:=<SN1>
ros2 launch caddy_ai2_ros2_camera_zed_2i zed_2i.launch.py camera_name:=zed_2i_right serial_number:=<SN2>
```

Con dos cámaras, `serial_number` es obligatorio.
