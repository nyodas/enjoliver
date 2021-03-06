package main

import (
	"testing"
)

func TestFormatProbeName(t *testing.T) {
	testCases := [][]string{
		{"FLEET_ETCD_CLIENT_PORT", "FleetEtcdClient"},
		{"KUBERNETES_ETCD_CLIENT_PORT", "KubernetesEtcdClient"},
		{"VAULT_ETCD_CLIENT_PORT", "VaultEtcdClient"},
		{"KUBERNETES_API_SERVER_PORT", "KubernetesApiServer"},
		{"KUBELET_PORT", "Kubelet"},
		{"VAULT_PORT", "Vault"},
	}
	var s string

	for _, elt := range testCases {
		s = formatProbeName(elt[0])
		if s != elt[1] {
			t.Errorf("fail %s", s)
		}
	}
}
