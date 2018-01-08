#!/usr/bin/env python3

import subprocess
import re
import xml.etree.ElementTree as et
import datetime as dt
import pipes
import os
import configparser
import sys

class TmuxError(Exception):
    pass

class TmuxCommandError(TmuxError):
    pass

class TmuxParseError(TmuxError):
    pass

class ConfigError(Exception):
    pass

def list_sessions_cmd():
    command = [
        'tmux',
        'list-sessions',
        '-F',
        '#{session_attached} #{session_created} #{session_name}',
    ]
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = process.communicate()
        out = out.decode('utf-8')
        err = err.decode('utf-8')
    except Exception as ex:
        raise TmuxCommandError(repr(ex).strip())
    if process.returncode == 0:
        return out
    if  'no server running' in err:
        return ''
    if re.search(r'^error connecting to .+ \(No such file or directory\)$', err):
        return ''
    raise TmuxCommandError(err.strip())

def parse_sessions(text):
    return [parse_session_line(l) for l in text.splitlines()]

def parse_session_line(line):
    match = re.search(
        '^(?P<attached>[01]) (?P<timestamp>[0-9]+) (?P<name>.*)$',
        line
    )
    if match is None:
        raise TmuxParseError('parse error: ' + line)
    return match.groupdict()

def session_list_to_xml(sessions):
    if not sessions:
        return error_message_to_xml('no sessions')
    root = et.Element('openbox_pipe_menu')
    cmd_tpl = reattach_cmd_template()
    for s in sessions:
        item = et.SubElement(root, 'item')
        item.attrib['label'] = session_label(s)
        action = et.SubElement(item, 'action')
        action.attrib['name'] = 'Execute'
        command = et.SubElement(action, 'command')
        # the command is parsed with the g_shell_parse_argv funcion
        # and therefore must have shell quoting (even though it does
        # not spawn a shell)
        command.text = cmd_tpl % pipes.quote(s['name'])
    return et.tostring(root)

def session_label(s):
    label = s['name'] + ' started at '
    label += dt.datetime.fromtimestamp(float(s['timestamp'])).isoformat()
    if int(s['attached']):
        label += ' (attached)'
    return label

def reattach_cmd_template():
    config = configparser.RawConfigParser()
    config.read(os.path.expanduser('~/.config/openbox/tmux.ini'))
    try:
        return config.get('pipe-menu', 'attach-command-template')
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass
    term = find_executable(['urxvt', 'xterm'])
    if term is None:
        raise ConfigError("can't find terminal emulator")
    return term + ' -e tmux attach -d -t %s'

def error_message_to_xml(message):
    root = et.Element('openbox_pipe_menu')
    item = et.SubElement(root, 'item')
    item.attrib['label'] = message
    return et.tostring(root)

def find_executable(names):
    path = os.environ.get("PATH", os.defpath).split(os.pathsep)
    for name in names:
        for d in path:
            f = os.path.join(d, name)
            if os.path.exists(f):
                return f

def main():
    try:
        xml = session_list_to_xml(parse_sessions(list_sessions_cmd()))
    except (TmuxError, ConfigError) as err:
        err_msg = err.message if hasattr(err, 'message') else str(err)
        xml = error_message_to_xml(err_msg)
    sys.stdout.buffer.write(xml)

if __name__ == '__main__':
    main()
