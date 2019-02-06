#!/usr/bin/env python3

import subprocess
import re
import xml.etree.ElementTree as et
import datetime as dt
import pipes
import os
import configparser
import sys
from typing import Iterable, Optional, Dict

class TmuxError(Exception):
    pass

class TmuxCommandError(TmuxError):
    pass

class TmuxParseError(TmuxError):
    pass

class ConfigError(Exception):
    pass

def list_sessions_cmd() -> str:
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
        return out # type: ignore
    if  'no server running' in err:
        return ''
    if re.search(r'^error connecting to .+ \(No such file or directory\)$', err):
        return ''
    raise TmuxCommandError(err.strip())

def parse_sessions(text: str) -> Iterable[Dict[str, str]]:
    return [parse_session_line(l) for l in text.splitlines()]

def parse_session_line(line: str) -> Dict[str, str]:
    match = re.search(
        '^(?P<attached>[0-9]+) (?P<timestamp>[0-9]+) (?P<name>.*)$',
        line
    )
    if match is None:
        raise TmuxParseError('parse error: ' + line)
    return match.groupdict()

def session_list_to_xml(sessions: Iterable[dict]) -> bytes:
    if not sessions:
        return error_message_to_xml('no sessions')
    root = et.Element('openbox_pipe_menu')
    cmd_tpl = reattach_cmd_template()
    for session in sessions:
        item = et.SubElement(root, 'item')
        item.attrib['label'] = session_label(session)
        action = et.SubElement(item, 'action')
        action.attrib['name'] = 'Execute'
        command = et.SubElement(action, 'command')
        # the command is parsed with the g_shell_parse_argv funcion
        # and therefore must have shell quoting (even though it does
        # not spawn a shell)
        command.text = cmd_tpl % pipes.quote(session['name'])
    return et.tostring(root) # type: ignore

def session_label(session: Dict[str, str]) -> str:
    label = session['name'] + ' started at '
    label += dt.datetime.fromtimestamp(float(session['timestamp'])).isoformat()
    if int(session['attached']):
        label += ' (attached)'
    return label

def reattach_cmd_template() -> str:
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

def error_message_to_xml(message: str) -> bytes:
    root = et.Element('openbox_pipe_menu')
    item = et.SubElement(root, 'item')
    item.attrib['label'] = message
    return et.tostring(root) # type: ignore

def find_executable(names: Iterable[str]) -> Optional[str]:
    path = os.environ.get("PATH", os.defpath).split(os.pathsep)
    for name in names:
        for directory in path:
            filename = os.path.join(directory, name)
            if os.path.exists(filename):
                return filename
    return None

def main() -> None:
    try:
        xml = session_list_to_xml(parse_sessions(list_sessions_cmd()))
    except (TmuxError, ConfigError) as err:
        xml = error_message_to_xml(repr(err))
    sys.stdout.buffer.write(xml)

if __name__ == '__main__':
    main()
