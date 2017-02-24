import copy
import os
import sys
import time
import unittest

from app import generator, schedulerv2, sync_matchbox

try:
    import kvm_player
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kvm_player


class TestKVMK8sFast(kvm_player.KernelVirtualMachinePlayer):
    @classmethod
    def setUpClass(cls):
        cls.check_requirements()
        cls.set_acserver()
        cls.set_rack0()
        cls.set_api()
        cls.set_matchbox()
        cls.set_dnsmasq()
        cls.pause(cls.wait_setup_teardown)


# @unittest.skip("")
class TestKVMK8SFast0(TestKVMK8sFast):
    # @unittest.skip("just skip")
    def test_00(self):
        self.assertEqual(self.fetch_discovery_interfaces(), [])
        nb_node = 3
        marker = "euid-%s-%s" % (TestKVMK8sFast.__name__.lower(), self.test_00.__name__)
        nodes = ["%s-%d" % (marker, i) for i in xrange(nb_node)]
        gen = generator.Generator(
            api_uri=self.api_uri,
            profile_id="%s" % marker,
            name="%s" % marker,
            ignition_id="%s.yaml" % marker,
            matchbox_path=self.test_matchbox_path
        )
        gen.dumps()
        sync = sync_matchbox.ConfigSyncSchedules(
            api_uri=self.api_uri,
            matchbox_path=self.test_matchbox_path,
            ignition_dict={
                "etcd_member_kubernetes_control_plane": "%s-%s" % (marker, "k8s-control-plane"),
                "kubernetes_nodes": "%s-%s" % (marker, "k8s-node")
            }
        )
        for m in nodes:
            destroy, undefine = ["virsh", "destroy", m], \
                                ["virsh", "undefine", m]
            self.virsh(destroy, v=self.dev_null), self.virsh(undefine, v=self.dev_null)
        try:
            for i, m in enumerate(nodes):
                virt_install = [
                    "virt-install",
                    "--name",
                    "%s" % m,
                    "--network=bridge:rack0,model=virtio",
                    "--memory=%d" % self.get_optimized_memory(nb_node),
                    "--vcpus=2",
                    "--pxe",
                    "--disk",
                    "none",
                    "--os-type=linux",
                    "--os-variant=generic",
                    "--noautoconsole",
                    "--boot=network"
                ]
                self.virsh(virt_install, assertion=True, v=self.dev_null)
                time.sleep(self.kvm_sleep_between_node)

            sch_cp = schedulerv2.EtcdMemberKubernetesControlPlane(self.api_uri)
            sch_cp.expected_nb = 1
            for i in xrange(60):
                if sch_cp.apply() is True:
                    sync.apply()
                    break
                time.sleep(self.kvm_sleep_between_node)

            self.assertTrue(sch_cp.apply())
            sch_no = schedulerv2.KubernetesNode(self.api_uri, apply_dep=False)
            for i in xrange(60):
                if sch_no.apply() == nb_node - 1:
                    break
                time.sleep(self.kvm_sleep_between_node)
            self.assertEqual(nb_node - 1, sch_no.apply())
            sync.apply()

            to_start = copy.deepcopy(nodes)
            self.kvm_restart_off_machines(to_start)
            time.sleep(self.kvm_sleep_between_node * nb_node)

            self.etcd_member_len(sync.kubernetes_control_plane_ip_list[0], sch_cp.expected_nb,
                                 self.ec.kubernetes_etcd_client_port)
            self.etcd_member_len(sync.kubernetes_control_plane_ip_list[0], sch_cp.expected_nb,
                                 self.ec.fleet_etcd_client_port)
            self.etcd_endpoint_health(sync.kubernetes_control_plane_ip_list + sync.kubernetes_nodes_ip_list,
                                      self.ec.kubernetes_etcd_client_port)
            self.etcd_endpoint_health(sync.kubernetes_control_plane_ip_list + sync.kubernetes_nodes_ip_list,
                                      self.ec.fleet_etcd_client_port)
            self.k8s_api_health(sync.kubernetes_control_plane_ip_list)
            self.etcd_member_k8s_minions(sync.kubernetes_control_plane_ip_list[0], nb_node)
            self.write_ending(marker)
        finally:
            if os.getenv("TEST"):
                self.iteractive_usage(
                    api_server_uri="http://%s:8080" % sync.kubernetes_control_plane_ip_list[0],
                    # fns=[sch_cp.apply, sch_no.apply, sync.apply]
                )
            for i in xrange(nb_node):
                machine_marker = "%s-%d" % (marker, i)
                destroy, undefine = ["virsh", "destroy", "%s" % machine_marker], \
                                    ["virsh", "undefine", "%s" % machine_marker]
                self.virsh(destroy), os.write(1, "\r")
                self.virsh(undefine), os.write(1, "\r")


if __name__ == "__main__":
    unittest.main(defaultTest=os.getenv("TEST"))
