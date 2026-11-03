# caddy_ai2_ros2_camera_zed_2i

Cámara estéreo **Stereolabs ZED 2i** para el Caddy AI2, siguiendo la estructura de
`caddy_ai2_ros2_sensors_rs_helios_5515`. Un único paquete que se instancia varias veces
(una entrada por cámara en `robot_params.yaml`).

**Licencia:** [CC BY 4.0](LICENSE.MD)

## Estado

| Parte | Estado |
|---|---|
| Simulación (Gazebo Harmonic `rgbd_camera` → imagen, profundidad, nube de puntos) | ✅ escrita, **sin probar todavía en Gazebo** |
| Launch del hardware real (envuelve `zed-ros2-wrapper`) | ✅ escrito, **sin probar en la ZED Box** |
| Dockerfile / contenedor para el Jetson Orin NX | ⏳ pendiente |
| Malla oficial de la cámara | ⏳ pendiente (caja provisional) |

## Contenido

```
description/sensor.urdf.j2          # link + joint + frame óptico + sensor rgbd_camera (Jinja2)
bringup/config/sensor_params.yaml   # parámetros operativos (hardware real) y de simulación
bringup/launch/zed_2i.launch.py     # hardware real: zed_wrapper con camera_name y serial_number
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

Requiere `zed_wrapper` y el ZED SDK dentro del contenedor del Jetson, no en el workspace de simulación.

```bash
ros2 launch caddy_ai2_ros2_camera_zed_2i zed_2i.launch.py camera_name:=zed_2i_left  serial_number:=<SN1>
ros2 launch caddy_ai2_ros2_camera_zed_2i zed_2i.launch.py camera_name:=zed_2i_right serial_number:=<SN2>
```

Con dos cámaras, `serial_number` es obligatorio.
