Display a [dynamic menu](http://openbox.org/wiki/Help:Menus#Dynamic_menus)
of [tmux](https://tmux.github.io/) sessions in the
[Openbox window manager](http://openbox.org/).

## Setup

Add the following to your Openbox menu configuration file,
`~/.config/openbox/menu.xml`:

	<menu id="tmux-sessions" label="tmux sessions" execute="~/path/openbox-tmux-pipe-menu.py" />

Reload Openbox configuration:

	openbox --reconfigure

## Usage

Selecting a session from the menu reattaches it in a new terminal window.

## Optional advanced configuration

By default, the command used to reattach a session is `tmux attach -d -t
$SESSION_NAME`. The command is run using urxvt or xterm.

This can be customized by creating a configuration file,
`~/.config/openbox/tmux.ini`, with a `pipe-menu` section containing an
`attach-command-template` value. A `%s` sequence in the command template
will be replaced with selected session name.

Example:

	[pipe-menu]
	attach-command-template = urxvt -T tmux-reattach -e tmux attach -d -t %s

This will reattach the selected session using a new urxvt window with the
title set to _tmux-reattach_. The title can then be used to further customize
the urxvt window with
[Openbox per-app settings](http://openbox.org/wiki/Help:Applications).
