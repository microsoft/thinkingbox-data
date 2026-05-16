# thinkingbox-data/servers

MCP servers to use with thinkingbox.

Each directory is a python package containing one or more MCP servers.

This `servers/` folder is expected to have the following structure (example with one server package, `thinkingbox_tools`):

```
thinkingbox-data/
  servers/
    thinkingbox_tools/  # a group of related servers, in this case the main body of ThinkingBox tests
        tests/  # unit tests for the servers in thinkingbox_tools
            test_cloud_drive_server.py  # unit tests for the cloud drive tools server
            ...
        thinkingbox_tools/  # groups all mcp servers in this folder under a common python package
            toolslib/ # support code for the MCP servers
                cloud_drive.py  # Support system/storage/logic for the mcp_cloud_drive.py tools server
                ...
            __init__.py
            mcp_cloud_drive.py  # MCP server for cloud drive tools
            ...
        pyproject.toml  # dependencies for the thinkingbox_tools package (inc. all server dependencies)
    servers.yaml  # configuration file for MCP Session Proxy, all servers must be listed here
```

