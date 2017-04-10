$(function() {
    function GCodeSystemCommandsViewModel(parameters) {
        var self = this;

        self.global_settings = parameters[0];

        self.command_definitions = ko.observableArray();

        self.addCommandDefinition = function() {
            self.command_definitions.push({id: 0, command:""});
        };

        self.removeCommandDefinition = function(definition) {
            self.command_definitions.remove(definition);
        };

        self.onBeforeBinding = function () {
            self.global_settings.settings.plugins.gcodesystemcommands.command_definitions.subscribe(function() {
                settings = self.global_settings.settings.plugins.gcodesystemcommands;
                self.command_definitions(settings.command_definitions.slice(0));            
            });
        };

        self.onSettingsBeforeSave = function () {
            self.global_settings.settings.plugins.gcodesystemcommands.command_definitions(self.command_definitions.slice(0));
        };

    }

    ADDITIONAL_VIEWMODELS.push([
        GCodeSystemCommandsViewModel,
        ["settingsViewModel"],
        ["#settings_plugin_gcodesystemcommands"]
    ]);
});
