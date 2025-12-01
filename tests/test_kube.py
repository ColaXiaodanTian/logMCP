import pytest
from src.kube import list_namespaces, list_pods, get_pod_logs, KubeError


class TestListNamespaces:
    def test_returns_list(self):
        result = list_namespaces()
        assert isinstance(result, list)

    def test_includes_default(self):
        result = list_namespaces()
        assert "default" in result

    def test_includes_kube_system(self):
        result = list_namespaces()
        assert "kube-system" in result


class TestListPods:
    def test_kube_system_has_pods(self):
        pods = list_pods("kube-system")
        assert len(pods) > 0

    def test_pod_has_required_fields(self):
        pods = list_pods("kube-system")
        pod = pods[0]
        assert "name" in pod
        assert "status" in pod
        assert "containers" in pod
        assert "restarts" in pod


class TestGetPodLogs:
    def test_fetches_logs(self):
        pods = list_pods("kube-system")
        pod_name = pods[0]["name"]

        logs = get_pod_logs(
            namespace="kube-system",
            pod=pod_name,
            tail_lines=10,
        )

        assert isinstance(logs, str)
