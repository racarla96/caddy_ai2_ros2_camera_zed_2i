"""Sanity check without Gazebo: renders the ZED camera URDF fragments (layouts A and B), the base URDF
and the bridge yaml, and checks frames, sensors and topic names.

Usage: python3 -I tools/check_render.py [WORKSPACE_SRC]   (default ~/caddy_ws/src)
Needs: jinja2, pyyaml. Does not need ROS or Gazebo."""
import copy
import math
import os
import sys
import xml.etree.ElementTree as ET

import yaml
from jinja2 import Environment, FileSystemLoader

WS = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/caddy_ws/src')
DESC = f'{WS}/caddy_ai2_ros2_description'
GZ = f'{WS}/caddy_ai2_ros2_gazebo_simulation'
CAM = f'{WS}/caddy_ai2_ros2_camera_zed_2i'

with open(f'{DESC}/bringup/config/robot_params.yaml') as f:
    params = yaml.safe_load(f)
with open(f'{CAM}/bringup/config/sensor_params.yaml') as f:
    cam_sp = yaml.safe_load(f)


def render_cameras(p, gazebo):
    out = []
    env = Environment(loader=FileSystemLoader(f'{CAM}/description'), keep_trailing_newline=True)
    for name, cfg in p['sensors'].items():
        if not cfg.get('enabled', True) or cfg['type'] != 'camera_rgbd':
            continue
        pose = cfg['pose']
        kw = dict(prefix='', sensor_name=name, frame_id=cfg['frame_id'], sensor_share=CAM,
                  x=pose['x'], y=pose['y'], z=pose['z'],
                  roll=pose['roll'], pitch=pose['pitch'], yaw=pose['yaw'], gazebo=gazebo)
        if gazebo:
            si = cam_sp['simulation']
            kw.update(namespace='', horizontal_fov=si['horizontal_fov'],
                      image_width=si['image_width'], image_height=si['image_height'],
                      range_min=si['range_min'], range_max=si['range_max'],
                      update_rate=si['update_rate'])
        out.append(env.get_template('sensor.urdf.j2').render(**kw))
    return '\n'.join(out)


def check(p, label, expected):
    for gazebo in (False, True):
        frag = render_cameras(p, gazebo)
        env = Environment(loader=FileSystemLoader(f'{DESC}/description/model/urdf'),
                          keep_trailing_newline=True)
        urdf = env.get_template('caddy_ai2_model.urdf.j2').render(
            namespace='', prefix='', sensors_urdf_fragment=frag, desc_share=DESC, **p)
        root = ET.fromstring(urdf)
        links = {l.get('name') for l in root.findall('link')}
        joints = {j.get('name'): j for j in root.findall('joint')}
        for cam in expected:
            assert f'{cam}_link' in links, (label, cam)
            assert f'{cam}_link_optical' in links, (label, cam)
            assert f'{cam}_joint' in joints and f'{cam}_optical_joint' in joints
        # every joint parent/child must exist
        for j in joints.values():
            assert j.find('parent').get('link') in links
            assert j.find('child').get('link') in links
        n_sensors = len(root.findall('.//sensor'))
        assert n_sensors == (len(expected) if gazebo else 0), (label, n_sensors)
        print(f'{label} gazebo={gazebo}: OK, {len(expected)} cameras, {n_sensors} gz sensors')

    env = Environment(loader=FileSystemLoader(f'{GZ}/bringup/config'), keep_trailing_newline=True)
    for ns, prefix in (('', ''), ('robot1', 'robot1_')):
        text = env.get_template('gz_msg_bridge.yaml.j2').render(
            namespace=ns, prefix=prefix, sensors=p['sensors'])
        entries = yaml.safe_load(text)
        cam_entries = [e for e in entries if '/zed_node/' in e['ros_topic_name']]
        assert len(cam_entries) == 4 * len(expected), (label, len(cam_entries))
        topics = [e['ros_topic_name'] for e in cam_entries]
        assert len(set(topics)) == len(topics)
        for e in cam_entries:
            assert e['frame_id'].startswith(prefix) and e['frame_id'].endswith('_optical')
        if ns == 'robot1':
            print('  sample:', cam_entries[0]['ros_topic_name'], '<-', cam_entries[0]['gz_topic_name'])
    print(f'{label}: bridge OK')


check(params, 'layout A', ['zed_2i_left', 'zed_2i_right'])

pb = copy.deepcopy(params)
for k in ('zed_2i_left', 'zed_2i_right'):
    pb['sensors'][k]['enabled'] = False
for k in ('zed_2i_front', 'zed_2i_rear'):
    pb['sensors'][k]['enabled'] = True
check(pb, 'layout B', ['zed_2i_front', 'zed_2i_rear'])

# Geometry check: FOV overlap / coverage for both layouts
H = cam_sp['simulation']['horizontal_fov']
aspect = cam_sp['simulation']['image_width'] / cam_sp['simulation']['image_height']
vfov = 2 * math.degrees(math.atan(math.tan(math.radians(H / 2)) / aspect))
print(f'vertical FOV with {cam_sp["simulation"]["image_width"]}x{cam_sp["simulation"]["image_height"]}: {vfov:.1f} deg')
theta = math.degrees(params['sensors']['zed_2i_left']['pose']['yaw'])
print(f'layout A: yaw {theta:.1f} deg -> overlap {H - 2*theta:.1f}, total {H + 2*theta:.1f}')
print(f'layout B: total {2*H:.0f}, blind sides 2x{(360 - 2*H)/2:.0f}')
