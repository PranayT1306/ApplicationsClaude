# ApplicationsClaude

A collection of applications built with the Claude (Anthropic) API and Oracle E-Business Suite.

## Setup

Each application reads its settings from a `json.config` file.
This file holds the API key and database login, so it is **not** stored in this repository.

1. Copy `json.config.example` into the application folder you want to run.
2. Rename the copy to `json.config`.
3. Fill in your own values (see below).

### Sample `json.config`

```json
{
  "params": {
    "anthropic_api_key": "api_key_get_from_console",
    "oracle_user": "apps",
    "oracle_password": "apps",
    "oracle_dsn": "hostname:portnumber/servicename"
  }
}
```

### Settings

| Setting | Description |
|---|---|
| `anthropic_api_key` | Your Claude API key from https://console.anthropic.com |
| `oracle_user` | Oracle database username |
| `oracle_password` | Oracle database password |
| `oracle_dsn` | Connection string in the format `hostname:port/service_name`, e.g. `ebsdb.example.com:1521/VIS` |

> **Never commit `json.config`.** It is already listed in `.gitignore`.
