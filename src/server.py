import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.kube import list_namespaces, list_pods, get_pod_logs, KubeError


server = Server("kubernetes-log-agent")

MAX_LOG_LENGTH = 8000


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_namespaces",
            description="List all namespaces in the Kubernetes cluster",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="list_pods",
            description="List pods in a namespace with status and restart count",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (e.g., 'default', 'kube-system')",
                    },
                },
                "required": ["namespace"],
            },
        ),
        Tool(
            name="get_pod_logs",
            description="Fetch recent logs from a Kubernetes pod for debugging",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Namespace of the pod",
                    },
                    "pod": {
                        "type": "string",
                        "description": "Pod name",
                    },
                    "container": {
                        "type": "string",
                        "description": "Container name (optional)",
                    },
                    "tail_lines": {
                        "type": "integer",
                        "description": "Number of recent lines (default 100, max 500)",
                    },
                },
                "required": ["namespace", "pod"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "list_namespaces":
            result = list_namespaces()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_pods":
            namespace = arguments.get("namespace", "default")
            result = list_pods(namespace)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_pod_logs":
            tail_lines = min(arguments.get("tail_lines", 100), 500)
            logs = get_pod_logs(
                namespace=arguments["namespace"],
                pod=arguments["pod"],
                container=arguments.get("container"),
                tail_lines=tail_lines,
            )

            if not logs.strip():
                return [TextContent(type="text", text="(No logs available)")]

            if len(logs) > MAX_LOG_LENGTH:
                logs = logs[:MAX_LOG_LENGTH] + "\\n\\n...[truncated]"

            return [TextContent(type="text", text=logs)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except KubeError as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


def main():
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
