# InfluxDB


https://docs.influxdata.com/influxdb/v2/install/?t=Windows&dl=oss&code_lang=powershell&code_lines=4&code_type=code&section=System%2520requirements&first_line=%2524acl%2520%253D%2520Get-Acl%2520%2522C%253A%255CUsers%255C%253Cusername%253E%255C.influxdbv2%2522&has_placeholders=true#download-and-install-influxdb-v2


```ps1

C:\Program Files\InfluxData

```

```ps1
   v1                   InfluxDB v1 management commands
   auth, authorization  Authorization management commands
   apply                Apply a template to manage resources
   stacks               List stack(s) and associated templates. Subcommands manage stacks.
   template             Summarize the provided template
   bucket-schema        Bucket schema management commands
   scripts              Scripts management commands
   ping                 Check the InfluxDB /health endpoint
   setup                Setup instance with initial user, org, bucket
   backup               Backup database
   restore              Restores a backup directory to InfluxDB
   remote               Remote connection management commands
   replication          Replication stream management commands
   server-config        Display server config
   help, h              Shows a list of commands or help for one command

GLOBAL OPTIONS:
   --help, -h  show help
PS C:\Program Files\InfluxData> .\influx.exe setup
Error: instance has already been set up
PS C:\Program Files\InfluxData> .\influx.exe config
Active  Name    URL                     Org
*       default http://localhost:8086
PS C:\Program Files\InfluxData> .\influx.exe config create
NAME:
   influx config create - Create config

USAGE:
   influx config create [command options] [arguments...]

DESCRIPTION:

The influx config create command creates a new InfluxDB connection configuration
and stores it in the configs file (by default, stored at ~/.influxdbv2/configs).

Authentication:
  Authentication can be provided by either an api token or username/password, but not both.
  When setting the username and password, the password is saved unencrypted in your local config file.
  Optionally, you can omit the password and only provide the username.
  You will then be prompted for the password each time.

Examples:
  # create a config and set it active
  influx config create -a -n $CFG_NAME -u $HOST_URL -t $TOKEN -o $ORG_NAME

  # create a config and without setting it active
  influx config create -n $CFG_NAME -u $HOST_URL -t $TOKEN -o $ORG_NAME

For information about the config command, see
https://docs.influxdata.com/influxdb/latest/reference/cli/influx/config/
and
https://docs.influxdata.com/influxdb/latest/reference/cli/influx/config/create/


COMMON OPTIONS:
   --configs-path value  Path to the influx CLI configurations [%INFLUX_CONFIGS_PATH%]
   --json                Output data as JSON [%INFLUX_OUTPUT_JSON%]
   --hide-headers        Hide the table headers in output data [%INFLUX_HIDE_HEADERS%]

OPTIONS:
   --config-name value, -n value        Name for the new config
   --host-url value, -u value           Base URL of the InfluxDB server the new config should target
   --token value, -t value              Auth token to use when communicating with the InfluxDB server
   --username-password value, -p value  Username (and optionally password) to use for authentication. Only supported in OSS
   --org value, -o value                Default organization name to use in the new config
   --active, -a                         Set the new config as active

Error: Required flags "config-name, host-url" not set
PS C:\Program Files\InfluxData> .\influx.exe completion
Error: usage: C:\Program Files\InfluxData\influx.exe completion [bash|zsh|powershell]
PS C:\Program Files\InfluxData> .\influx.exe completion powershell
Register-ArgumentCompleter -Native -CommandName C:\Program Files\InfluxData\influx.exe -ScriptBlock {
param($commandName, $wordToComplete, $cursorPosition)
     $other = "$wordToComplete --generate-bash-completion"
         Invoke-Expression $other | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
         }
 }
```