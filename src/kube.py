import subprocess
import json
from typing import Optional


class KubeError(Exception):
    """Raised when kubectl command fails."""
    pass


def run_kubectl(args: list[str], timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            ["kubectl"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise KubeError(f"kubectl timed out after {timeout}s")
    except FileNotFoundError:
        raise KubeError("kubectl not found. Is it installed?")

    if result.returncode != 0:
        raise KubeError(result.stderr.strip())

    return result.stdout


def list_namespaces() -> list[str]:
    raw = run_kubectl(["get", "namespaces", "-o", "json"])
    data = json.loads(raw)
    return [ns["metadata"]["name"] for ns in data["items"]]


def list_pods(namespace: str = "default") -> list[dict]:
    raw = run_kubectl(["get", "pods", "-n", namespace, "-o", "json"])
    data = json.loads(raw)

    return [
        {
            "name": p["metadata"]["name"],
            "namespace": namespace,
            "status": p["status"]["phase"],
            "containers": [c["name"] for c in p["spec"]["containers"]],
            "restarts": sum(
                cs.get("restartCount", 0)
                for cs in p["status"].get("containerStatuses", [])
            ),
        }
        for p in data["items"]
    ]


def get_pod_logs(
    namespace: str,
    pod: str,
    container: Optional[str] = None,
    tail_lines: int = 100,
) -> str:
    args = ["logs", "-n", namespace, pod, f"--tail={tail_lines}"]
    if container:
        args += ["-c", container]
    return run_kubectl(args)
