# coding=utf-8
from __future__ import absolute_import

__author__ = "Shawn Bruce <kantlivelong@gmail.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 Shawn Bruce - Released under terms of the AGPLv3 License"

import octoprint.plugin
import time
import os
import sys

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

    def hook_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if not gcode and cmd[:4].upper() == 'OCTO':
            cmd_pieces = cmd[4:].split(' ', 1)
            cmd_id = cmd_pieces[0]
            cmd_args = ""
            if len(cmd_pieces) > 1:
                cmd_args = cmd_pieces[1]

            try:
                cmd_line = self.command_definitions[cmd_id]
            except:
                self._logger.error("No definiton found for ID %s" % cmd_id)
                return (None,)

            self._logger.debug("Command ID=%s, Command Line=%s, Args=%s" % (cmd_id, cmd_line, cmd_args))

            self._logger.info("Executing command ID: %s" % cmd_id)
            comm_instance._log("Exec(GCodeSystemCommands): OCTO%s" % cmd_id)

            try:
                r = os.system("%s %s" % (cmd_line, cmd_args))
            except:
                e = sys.exc_info()[0]
                self._logger.exception("Error executing command ID %s: %s" % (cmd_id, e))
                return (None,)

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

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = GCodeSystemCommands()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.hook_gcode_queuing,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
