# coding=utf-8
from __future__ import absolute_import

__author__ = "Shawn Bruce <kantlivelong@gmail.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 Shawn Bruce - Released under terms of the AGPLv3 License"

import six

import octoprint.plugin
import time
import os
import sys
import subprocess
import re

class GCodeSystemCommands(octoprint.plugin.StartupPlugin,
                          octoprint.plugin.TemplatePlugin,
                          octoprint.plugin.AssetPlugin,
                          octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.command_definitions = {}


    def on_settings_initialized(self):
        self.reload_command_definitions()

    def reload_command_definitions(self):
        self.command_definitions = {}

        command_definitions_tmp = self._settings.get(["command_definitions"])
        self._logger.debug("command_definitions: %s" % command_definitions_tmp)

        for definition in command_definitions_tmp:
            cmd_id = definition['id']
            cmd_line = definition['command']
            self.command_definitions[cmd_id] = cmd_line
            self._logger.info("Add command definition OCTO%s = %s" % (cmd_id, cmd_line))

    def hook_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if gcode:
            return

        if cmd[:4] != 'OCTO':
            return

        match = re.search(r'^(OCTO[0-9]+)(?:\s(.*))?$', cmd)
        if match is None:
            return

        cmd_id = match.group(1)[4::]
        cmd_args = match.group(2)

        try:
            cmd_line = self.command_definitions[cmd_id]
        except:
            self._logger.error("No definition found for ID %s" % cmd_id)
            comm_instance._log("Return(GCodeSystemCommands): undefined")
            return (None,)

        self._logger.debug("Command ID=%s, Line=%s, Args=%s" % (cmd_id, cmd_line, cmd_args))

        self._logger.info("Executing command ID: %s" % cmd_id)
        comm_instance._log("Exec(GCodeSystemCommands): OCTO%s" % cmd_id)

        cmd_env = {}
        cmd_env['OCTOPRINT_GCODESYSTEMCOMMAND_ID'] = str(cmd_id)
        cmd_env['OCTOPRINT_GCODESYSTEMCOMMAND_ARGS'] = str(cmd_args) if cmd_args else ''
        cmd_env['OCTOPRINT_GCODESYSTEMCOMMAND_LINE'] = str(cmd)

        try:
            p = subprocess.Popen(cmd_line, env=cmd_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            output = p.communicate()[0]
            r = p.returncode
        except:
            e = sys.exc_info()[0]
            self._logger.exception("Error executing command ID %s: %s" % (cmd_id, e))
            return (None,)

        # Make sure we don't throw when logging output if it contains non-ascii characters
        output = six.ensure_text(output, "utf-8", "ignore")

        self._logger.debug("Command ID %s returned: %s, output=%s" % (cmd_id, r, output))
        self._logger.info("Command ID %s returned: %s" % (cmd_id, r))

        if r == 0:
            status = 'ok'
        else:
            status = 'error'

        comm_instance._log("Return(GCodeSystemCommands): %s" % status)

        return (None,)

    def get_settings_defaults(self):
        return dict(
            command_definitions = []
        )

    def get_settings_restricted_paths(self):
        return dict(admin=[["command_definitions"]])

    def on_settings_load(self):
        data = octoprint.plugin.SettingsPlugin.on_settings_load(self)

        # only return our restricted settings to admin users - this is only needed for OctoPrint <= 1.2.16
        restricted = ("command_definitions")
        for r in restricted:
            if r in data and (current_user is None or current_user.is_anonymous() or not current_user.is_admin()):
                data[r] = None

        return data

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_command_definitions()

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=True)
        ]

    def get_assets(self):
        return {
            "js": ["js/gcodesystemcommands.js"]
        }

    def get_update_information(self):
        return dict(
            gcodesystemcommands=dict(
                displayName="GCode System Commands",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="kantlivelong",
                repo="OctoPrint-GCodeSystemCommands",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/kantlivelong/OctoPrint-GCodeSystemCommands/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "GCODE System Commands"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = GCodeSystemCommands()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.hook_gcode_sending,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
