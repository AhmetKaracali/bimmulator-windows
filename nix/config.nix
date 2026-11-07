let
  configFile = builtins.getEnv "IDRIVE_CONFIG_FILE";
in
builtins.fromTOML (builtins.readFile configFile)
