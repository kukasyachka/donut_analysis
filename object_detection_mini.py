import os

import pandas as pd
import yaml


def get_df(filename):
    df = pd.read_csv(filename, comment='#')
    return df


def parse_obj_detection_yaml(fname):
    with open(fname, mode='r') as fd:
        buf = fd.read(10000)
        comment_lines = []
        in_yaml_comment = False
        lines = buf.strip().split('\n')
        for idx, line in enumerate(lines):
            if line.startswith('# -- start of object detection yaml config --'):
                in_yaml_comment = True
                end_yaml_str = '# -- end of object detection yaml config --'
                continue
            elif line.startswith('# -- start of yaml config --'):
                in_yaml_comment = True
                end_yaml_str = '# -- end of yaml config --'
                continue
            if in_yaml_comment:
                if line.startswith(end_yaml_str):
                    break
                assert line[0:2] == '# '
                comment_lines.append(line[2:])
        yaml_buf = '\n'.join(comment_lines)
        yaml_data = yaml.safe_load(yaml_buf)
    return yaml_data


def load(fname, t_from=None, t_to=None):    
    """
    :param fname: object detection file name (flytrax*.csv)
    :param t_from: first valid second of recording
    :param t_to: last valid second of redcording
    :return: yaml_data (dict), pandas DataFrame
    """

    # TODO: version: 0.20.29" no timestamp column, but time in microseconds
    # time_microseconds,frame,x_px,y_px,orientation_radians_mod_pi,central_moment,led_1,led_2,led_3
    yaml_data, df = parse_obj_detection_yaml(fname), get_df(fname)
    app_data = yaml_data.get('app', None)
    obj_detection_config = yaml_data.get('object_detection_cfg', yaml_data)

    version = '0'
    if app_data is not None:
        version = app_data['version']
        print('ver', version)
    # if version>='0.20.29':
    #     df['timestamp'] = df.time_microseconds
    if 'timestamp' in df.columns:
        df['t'] = df.timestamp - df.timestamp.iloc[0]
    if 'time_microseconds' in df.columns:
        df['timestamp'] = 1e-6*df.time_microseconds
        df['t'] = df.timestamp - df.timestamp.iloc[0]

    if t_from is not None:
        df = df[df.t >= t_from]
    if t_to is not None:
        df = df[df.t < t_to]
    print('time: [{}, {}]'.format(df.t.iloc[0], df.t.iloc[-1]))
    return obj_detection_config, df


def load_with_arena(fname, t_from=None, t_to=None, nbins=None):    
    """
    :param fname: object detection file name (flytrax*.csv)
    :param t_from: first valid second of recording
    :param t_to: last valid second of redcording
    :return: arena: WalkingFlyArena , df: pandas DataFrame
    """
    from flydance.analysis.arena import create_arena_from_yaml_data
    od, df = load(fname, t_from, t_to)
    arena = create_arena_from_yaml_data(od)
    if nbins is not None:
        arena.xy_binning(nbins, nbins)
        arena.objects['bins']['visible'] = False
    return arena, df


def load_arena_from_flytrax(fname, nbins=None):
    from flydance.analysis.arena import create_arena_from_yaml_data
    yaml_data = parse_obj_detection_yaml(fname)
    obj_detection_config = yaml_data.get('object_detection_cfg', yaml_data)
    arena = create_arena_from_yaml_data(obj_detection_config)
    if nbins is not None:
        arena.xy_binning(nbins, nbins)
        arena.objects['bins']['visible'] = False

    return arena