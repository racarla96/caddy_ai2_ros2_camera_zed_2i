# Traspaso: cámaras ZED 2i en el Caddy AI2

Documento para continuar el trabajo en otra sesión de Claude Code. Estado a 2026-11-03.

## Objetivo

Integrar dos ZED 2i, montadas en la barra superior del Caddy AI2, en la simulación (Gazebo Harmonic) y
preparar el driver real para la Jetson Orin NX. Hay que **estudiar qué disposición de las dos cámaras
conviene**, así que ambas están definidas y se alterna entre ellas.

## Contexto del proyecto

- ROS 2 **Jazzy**, Gazebo Harmonic. Fuente única de verdad de la geometría: `caddy_ai2_ros2_description/bringup/config/robot_params.yaml`, renderizada con Jinja2 al lanzar (sin recompilar).
- Paquetes propios: `ament_cmake`, licencia **CC BY 4.0** (titular "racarla96 - Rafael Carbonell Lázaro"), prefijo `caddy_ai2_ros2_`.
- Un repo por sensor y un workspace de integración (`caddy_ai2_ros2_sim`) con todo como submódulos git.
- Jetson Orin NX / ZED Box: JetPack 6.2 (Ubuntu 22.04) **sin reflashear**; el stack de sensores va en un contenedor Docker con ROS 2 Jazzy. Solo el contenedor de sensores corre en la Jetson; tracción e interfaz van en otro PC. Imágenes en Docker Hub bajo `racarla96`. Repo orquestador previsto: `caddy_ai2_ros2_zedbox_sensors`.
- El ZED SDK **no corre en Gazebo**: en simulación la cámara es un sensor `rgbd_camera` de Gazebo.

## Repos y ramas

| Repo | Rama | Qué cambia |
|---|---|---|
| `caddy_ai2_ros2_camera_zed_2i` | `main` | Paquete nuevo: `description/sensor.urdf.j2`, `bringup/config/sensor_params.yaml`, `bringup/launch/zed_2i.launch.py`, `tools/`, `scripts/`, estos docs |
| `caddy_ai2_ros2_description` | `feat/zed-2i-cameras` | 4 cámaras en `robot_params.yaml` (sección `sensors`, `type: camera_rgbd`) y tabla del README |
| `caddy_ai2_ros2_gazebo_simulation` | `feat/zed-2i-cameras` | Rama `camera_rgbd` en `spawn_robot.launch.py` y bridges por cámara en `gz_msg_bridge.yaml.j2` |
| `caddy_ai2_ros2_sim` | `feat/zed-2i-cameras` | Submódulo de la cámara, punteros de submódulos y README |

Las ramas `feat/...` **no están fusionadas** en `jazzy`. No hay PRs abiertos todavía.

## Las dos disposiciones

Solo una pareja activa a la vez (`enabled: true`); la otra en `false`. FOV horizontal H = 110° (objetivo de 2,1 mm).

| | A (activa por defecto) | B |
|---|---|---|
| Cámaras | `zed_2i_left`, `zed_2i_right`: delanteras, en los extremos, yaw ±40° hacia fuera | `zed_2i_front`, `zed_2i_rear`: centradas, yaw 0° y 180° |
| Cobertura | 190°, solape central 30° | 220°, sin solape, 2 × 70° ciegos en los laterales |

Con yaw ±θ hacia fuera: solape = H − 2θ, cobertura = H + 2θ. Poses **provisionales** (x 0,6, y ±0,5, z 1,45 m respecto a `base_link`): faltan las medidas reales de la barra.

## Topics y frames

Por cámara, con `<cam>` = clave del sensor (`zed_2i_left`, ...):

```
/<ns>/<cam>/zed_node/left/color/rect/image          sensor_msgs/Image
/<ns>/<cam>/zed_node/left/color/rect/camera_info    sensor_msgs/CameraInfo
/<ns>/<cam>/zed_node/depth/depth_registered         sensor_msgs/Image
/<ns>/<cam>/zed_node/point_cloud/cloud_registered   sensor_msgs/PointCloud2
```

Frames: `<frame_id>` (x adelante) y `<frame_id>_optical` (z adelante), este último es el `frame_id` de las imágenes.
Gazebo publica `/<ns>/<cam>/rgbd/{image,depth_image,points,camera_info}` y el bridge los renombra.

## Qué está verificado y qué no

Verificado (sin ROS ni Gazebo, con `python3 -I tools/check_render.py [WS/src]`): las plantillas se renderizan para A y B, el URDF es XML válido con todos los joints enlazados, hay un sensor Gazebo por cámara activa, el bridge genera 4 entradas por cámara con nombres únicos y con prefijo/namespace, y la geometría (solape y cobertura) sale como se esperaba.

Verificado además contra el código vendorizado (`third_party/zed-ros2-wrapper`, v5.5.0-22): `zed_camera.launch.py` declara `camera_name`, `camera_model`, `serial_number`, `publish_urdf`, `publish_tf` y `publish_map_tf`. Ojo: `operation.grab_*` de `sensor_params.yaml` no se pasa al wrapper (su `zed2i.yaml` usa 60 fps).

**No verificado:**
- Que Gazebo arranque con los sensores y que el bridge `ros_gz_bridge` los acepte (en particular `gz.msgs.CameraInfo` y `PointCloudPacked` desde `rgbd_camera`).
- Que los nombres de topics del bridge coincidan con los `gz_topic_name` reales que publica `rgbd_camera` (se asumió `<topic>/image`, `/depth_image`, `/points`, `/camera_info`).
- Nada del hardware real.

## Riesgo conocido: frames reales frente a simulados

El wrapper real etiqueta sus imágenes con sus propios frames ópticos (nombres derivados de `camera_name`),
y `zed_2i.launch.py` lo lanza con `publish_urdf:=false`. Si no coinciden con `<frame_id>_optical` del URDF del robot,
la nube de puntos real no se podrá transformar a `base_link`. Hay que reconciliarlo al probar en hardware
(o renombrar el frame en el URDF, o dejar que el wrapper publique su URDF colgado del de la barra).

## Pendiente

1. **Probar en Gazebo** (`sim.launch.py`) con cada disposición; mirar imágenes y solape en RViz. Ajustar `gz_topic_name` si no coinciden.
2. **Medir la barra** y poner las poses reales.
3. **Decidir la disposición** (A o B) y dejarla como única; opcionalmente generar las dos por launch argument en vez de editar el yaml.
4. **Contenedor Jetson** (no iniciado): ZED SDK 5.x para L4T 36 (JetPack 6.2) + `zed-ros2-wrapper` + ROS 2 Jazzy. Jazzy es para Ubuntu 24.04 y la base L4T 36 es 22.04, así que el contenedor lo construye a medida; el repo orquestador `caddy_ai2_ros2_zedbox_sensors` combina los sensores.
5. Con dos cámaras reales hace falta `serial_number` distinto en cada lanzamiento.
6. Malla visual de la ZED 2i (ahora es una caja) e IMU de la cámara en simulación (no está).
7. Abrir PRs de las ramas `feat/zed-2i-cameras` y, al fusionarlas, actualizar los punteros del repo `sim`.

## Driver vendorizado

`third_party/zed-ros2-wrapper` es submódulo del fork `racarla96/zed-ros2-wrapper` (rama `master`, remoto `upstream` = stereolabs). Colcon no lo ve (el paquete padre bloquea el descenso) y el sim no lo compila: necesita ZED SDK. Actualizar: `gh repo sync racarla96/zed-ros2-wrapper -b master`, `git -C third_party/zed-ros2-wrapper pull`, commit del puntero.

## Trampas del workspace

- **No ejecutes `git submodule update --remote`** en `caddy_ai2_ros2_sim` mientras las ramas no estén fusionadas: movería `description` y `gazebo_simulation` al final de `jazzy` y desaparecerían las cámaras.
- El puntero de `caddy_ai2_ros2_bicycle_to_ackermann_traction_adapter` en la rama `jazzy` de `sim` (`5017987`) **no existe en GitHub** (el remoto tiene `c05ef17` en `jazzy`). Una clonación limpia con `--recurse-submodules` falla en ese submódulo; el resto se clona bien. Probablemente falta un `git push` en ese repo o hay que actualizar el puntero.
- `.gitmodules` usa URLs SSH (`git@github.com:`). Sin clave SSH: `USE_HTTPS=1 scripts/setup_workspace.sh`.

## Cómo instalarlo

```bash
# Este equipo (simulación completa)
scripts/setup_workspace.sh ~/caddy_ws sim

# Jetson Orin NX (solo este paquete; el ZED SDK y el wrapper van en el contenedor, aún pendiente)
scripts/setup_workspace.sh ~/caddy_ws jetson
```

Comprobación rápida sin ROS: `python3 -I tools/check_render.py ~/caddy_ws/src`.
