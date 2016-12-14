import os
import subprocess
from unittest import TestCase

from app import generate_profiles, generate_common


class IOErrorToWarning(object):
    def __enter__(self):
        generate_common.GenerateCommon._raise_enof = Warning

    def __exit__(self, ext, exv, trb):
        generate_common.GenerateCommon._raise_enof = IOError





class TestGenerateProfiles(TestCase):
    gen = generate_profiles.GenerateProfile
    network_environment = "%s/misc/network-environment" % gen.bootcfg_path
    unit_path = "%s" % os.path.dirname(__file__)
    tests_path = "%s" % os.path.split(unit_path)[0]
    test_bootcfg_path = "%s/test_bootcfg" % tests_path

    @classmethod
    def setUpClass(cls):
        os.environ["BOOTCFG_URI"] = "http://127.0.0.1:8080"
        os.environ["API_URI"] = "http://127.0.0.1:5000"
        subprocess.check_output(["make", "-C", cls.gen.project_path])
        # generate_common.GenerateCommon._raise_enof = Warning  # Skip the ignition isfile
        with IOErrorToWarning():
            cls.gen = generate_profiles.GenerateProfile(
                _id="etcd-proxy", name="etcd-proxy", ignition_id="etcd-proxy.yaml")
        # generate_common.GenerateCommon._raise_enof = IOError
        cls.gen.profiles_path = "%s/test_resources" % cls.tests_path

    def test_01_boot(self):
        expect = {
            'kernel': '%s/assets/coreos/serve/coreos_production_pxe.vmlinuz' % self.gen.bootcfg_uri,
            'initrd': ['%s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz' % self.gen.bootcfg_uri],
            'cmdline':
                {
                    'coreos.autologin': '',
                    'coreos.first_boot': '',
                    'coreos.oem.id': 'pxe',
                    'coreos.config.url': '%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}' % self.gen.bootcfg_uri
                }
        }
        self.gen._boot()

        self.assertEqual(expect, self.gen._target_data["boot"])

    def test_990_generate(self):
        expect = {
            "cloud_id": "",
            "boot": {
                "kernel": "%s/assets/coreos/serve/coreos_production_pxe.vmlinuz" % self.gen.bootcfg_uri,
                "initrd": [
                    "%s/assets/coreos/serve/coreos_production_pxe_image.cpio.gz" % self.gen.bootcfg_uri
                ],
                "cmdline": {
                    "coreos.autologin": "",
                    "coreos.first_boot": "",
                    "coreos.oem.id": "pxe",
                    "coreos.config.url": "%s/ignition?uuid=${uuid}&mac=${net0/mac:hexhyp}" %
                                         self.gen.bootcfg_uri
                }
            },
            "id": "etcd-proxy",
            "ignition_id": "etcd-proxy.yaml",
            "name": "etcd-proxy"
        }
        with IOErrorToWarning():
            new = generate_profiles.GenerateProfile(
                _id="etcd-proxy", name="etcd-proxy", ignition_id="etcd-proxy.yaml")
        result = new.generate()
        self.assertEqual(expect, result)

    def test_991_dump(self):
        _id = "etcd-test-%s" % self.test_991_dump.__name__
        with IOErrorToWarning():
            new = generate_profiles.GenerateProfile(
                _id="%s" % _id, name="etcd-test", ignition_id="etcd-test.yaml", bootcfg_path=self.test_bootcfg_path)
        new.dump()
        self.assertTrue(os.path.isfile("%s/profiles/%s.json" % (self.test_bootcfg_path, _id)))
        os.remove("%s/profiles/%s.json" % (self.test_bootcfg_path, _id))
