import json
import os
import shutil
import unittest

from app import api
from app import configs
from app import model
from common import posts

ec = configs.EnjoliverConfig(importer=__file__)


class TestAPI(unittest.TestCase):
    unit_path = os.path.dirname(os.path.abspath(__file__))
    dbs_path = "%s/dbs" % unit_path

    @classmethod
    def setUpClass(cls):
        try:
            os.remove(ec.db_path)
        except OSError:
            pass
        api.ignition_journal = "%s/ignition_journal" % cls.unit_path

        shutil.rmtree(api.ignition_journal, ignore_errors=True)

        engine = api.create_engine(ec.db_uri)
        model.Base.metadata.create_all(engine)
        api.engine = engine
        cls.app = api.app.test_client()

        cls.app.testing = True

    def test_healthz_00(self):
        expect = {
            u'flask': True,
            u'global': False,
            u'db': True,
            u'matchbox': {
                u'/boot.ipxe': False,
                u'/boot.ipxe.0': False,
                u'/': False,
                u'/assets': False,
                u"/metadata": False
            }}

        result = self.app.get('/healthz')
        self.assertEqual(result.status_code, 200)
        content = json.loads(result.data)
        self.assertEqual(content, expect)

    def test_ipxe_boot(self):
        expect = '#!ipxe\n' \
                 'echo start /boot.ipxe\n' \
                 ':retry_dhcp\n' \
                 'dhcp || goto retry_dhcp\n' \
                 'chain http://127.0.0.1:5000/ipxe?' \
                 'uuid=${uuid}&' \
                 'mac=${net0/mac:hexhyp}&' \
                 'domain=${domain}&' \
                 'hostname=${hostname}&' \
                 'serial=${serial}\n'

        result = self.app.get('/boot.ipxe')
        self.assertEqual(result.status_code, 200)
        content = result.data
        self.assertEqual(content, expect)

    def test_ipxe_boot_0(self):
        expect = '#!ipxe\n' \
                 'echo start /boot.ipxe\n' \
                 ':retry_dhcp\n' \
                 'dhcp || goto retry_dhcp\n' \
                 'chain http://127.0.0.1:5000/ipxe?' \
                 'uuid=${uuid}&' \
                 'mac=${net0/mac:hexhyp}&' \
                 'domain=${domain}&' \
                 'hostname=${hostname}&' \
                 'serial=${serial}\n'

        result = self.app.get('/boot.ipxe.0')
        self.assertEqual(result.status_code, 200)
        content = result.data
        self.assertEqual(content, expect)

    def test_ipxe(self):
        result = self.app.get('/ipxe?uuid=fake?mac=fake')
        self.assertEqual(result.status_code, 404)

    def test_404(self):
        result = self.app.get('/fake')
        self.assertEqual(result.status_code, 404)
        content = result.data
        self.assertEqual(content, "404")

    def test_root(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)

    def test_discovery_00(self):
        result = self.app.post('/discovery', data=json.dumps(posts.M01),
                               content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {u'total_elt': 1, u'new': True})
        result = self.app.post('/discovery', data=json.dumps(posts.M02),
                               content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {u'total_elt': 2, u'new': True})

    def test_discovery_01(self):
        discovery_data = "bad"
        result = self.app.post('/discovery', data=json.dumps(discovery_data),
                               content_type='application/json')
        self.assertEqual(result.status_code, 406)
        self.assertEqual(json.loads(result.data), {u'boot-info': {}, u'interfaces': [], u'lldp': {}})

    def test_discovery_02(self):
        for i in xrange(5):
            r = self.app.get("/discovery")
            self.assertEqual(200, r.status_code)
            data = json.loads(r.data)
            self.assertEqual(2, len(data))

    def test_discovery_03(self):
        r = self.app.get("/discovery/interfaces")
        self.assertEqual(200, r.status_code)
        data = json.loads(r.data)
        self.assertEqual(2, len(data))

    def test_discovery_04(self):
        uuid = posts.M01["boot-info"]["uuid"]
        r = self.app.get("/discovery/ignition-journal/%s" % uuid)
        self.assertEqual(200, r.status_code)
        data = json.loads(r.data)
        self.assertEqual(39, len(data))

    def test_discovery_06(self):
        r = self.app.get("/discovery/ignition-journal")
        self.assertEqual(200, r.status_code)
        data = json.loads(r.data)
        self.assertEqual(2, len(data))
        self.assertEqual(1, len(data[0]["boot_id_list"]))
        self.assertEqual(1, len(data[1]["boot_id_list"]))

    def test_discovery_06_more(self):
        r = self.app.get("/discovery/ignition-journal")
        self.assertEqual(200, r.status_code)
        data = json.loads(r.data)
        self.assertEqual(2, len(data))
        self.assertEqual(1, len(data[0]["boot_id_list"]))
        self.assertEqual(1, len(data[1]["boot_id_list"]))

        uuid = data[0]["uuid"]
        boot_id = data[0]["boot_id_list"][0]["boot_id"]
        r = self.app.get("/discovery/ignition-journal/%s/%s" % (uuid, boot_id))
        self.assertEqual(200, r.status_code)
        new_data = json.loads(r.data)
        self.assertEqual(39, len(new_data))

        uuid = data[1]["uuid"]
        boot_id = data[1]["boot_id_list"][0]["boot_id"]
        r = self.app.get("/discovery/ignition-journal/%s/%s" % (uuid, boot_id))
        self.assertEqual(200, r.status_code)
        new_data = json.loads(r.data)
        self.assertEqual(39, len(new_data))

    def test_discovery_05(self):
        r = self.app.get("/discovery")

        for m in json.loads(r.data):
            uuid = m["boot-info"]["uuid"]
            r = self.app.get("/discovery/ignition-journal/%s" % uuid)
            self.assertEqual(200, r.status_code)

    def test_scheduler_00(self):
        r = self.app.get("/scheduler")
        self.assertEqual(200, r.status_code)
        self.assertEqual({}, json.loads(r.data))

    def test_scheduler_01(self):
        r = self.app.post("/scheduler")
        self.assertEqual(406, r.status_code)
        self.assertEqual({
            u'roles': [
                u'etcd-member',
                u'kubernetes-control-plane',
                u'kubernetes-node'
            ],
            u'selector': {u'mac': u''}
        }, json.loads(r.data))

    def test_scheduler_02(self):
        mac = posts.M01["boot-info"]["mac"]
        data = {
            u'roles': [
                u'etcd-member',
                u'kubernetes-control-plane'
            ],
            u'selector': {u'mac': mac}
        }
        r = self.app.post("/scheduler", data=json.dumps(data),
                          content_type='application/json')
        self.assertEqual(200, r.status_code)
        self.assertEqual(data, json.loads(r.data))
        r = self.app.get("/scheduler")
        self.assertEqual({mac: [
            u'etcd-member',
            u'kubernetes-control-plane'
        ]}, json.loads(r.data))

    def test_scheduler_03(self):
        role = "etcd-member"
        r = self.app.get("/scheduler/%s" % role)
        self.assertEqual(1, len(json.loads(r.data)))
        r = self.app.get("/scheduler/ip-list/%s" % role)
        self.assertEqual(1, len(json.loads(r.data)))

    def test_scheduler_04(self):
        role = "kubernetes-control-plane"
        r = self.app.get("/scheduler/%s" % role)
        self.assertEqual(1, len(json.loads(r.data)))
        r = self.app.get("/scheduler/ip-list/%s" % role)
        self.assertEqual(1, len(json.loads(r.data)))

    def test_scheduler_05(self):
        role = "kubernetes-node"
        r = self.app.get("/scheduler/%s" % role)
        self.assertEqual(0, len(json.loads(r.data)))
        r = self.app.get("/scheduler/ip-list/%s" % role)
        self.assertEqual(0, len(json.loads(r.data)))

    def test_scheduler_06(self):
        role = "not-existing"
        r = self.app.get("/scheduler/%s" % role)
        self.assertEqual(0, len(json.loads(r.data)))
        r = self.app.get("/scheduler/ip-list/%s" % role)
        self.assertEqual(0, len(json.loads(r.data)))

    def test_scheduler_07(self):
        role = "etcd-member&kubernetes-control-plane"
        r = self.app.get("/scheduler/%s" % role)
        self.assertEqual(1, len(json.loads(r.data)))

    def test_scheduler_08(self):
        r = self.app.get("/scheduler/available")
        l = json.loads(r.data)
        self.assertEqual(1, len(l))
        for m in l:
            self.assertEqual([], m["roles"])

    def test_lifecycle_01(self):
        r = self.app.get("/lifecycle/coreos-install")
        self.assertEqual([], json.loads(r.data))

    def test_lifecycle_02(self):
        r = self.app.get("/lifecycle/ignition")
        self.assertEqual([], json.loads(r.data))

    def test_lifecycle_03(self):
        r = self.app.get("/lifecycle/rolling")
        self.assertEqual([], json.loads(r.data))

    def test_lifecycle_04(self):
        rawq = "mac=%s&uuid=%s&os=installed" % (
            posts.M01["boot-info"]["mac"].replace(":", "-"), posts.M01["boot-info"]["uuid"])
        r = self.app.post("/lifecycle/coreos-install/success/%s" % rawq)
        self.assertEqual(200, r.status_code)
        r = self.app.get("/lifecycle/coreos-install")
        d = json.loads(r.data)
        self.assertEqual(1, len(d))
        self.assertTrue(d[0]["success"])

    def test_lifecycle_04a(self):
        rawq = "mac=%s&uuid=%s&os=installed" % (
            posts.M02["boot-info"]["mac"].replace(":", "-"), posts.M02["boot-info"]["uuid"])
        r = self.app.post("/lifecycle/coreos-install/fail/%s" % rawq)
        self.assertEqual(200, r.status_code)
        r = self.app.get("/lifecycle/coreos-install")
        d = json.loads(r.data)
        self.assertEqual(2, len(d))
        self.assertTrue(d[0]["success"])
        self.assertFalse(d[1]["success"])

    def test_lifecycle_05(self):
        rawq = "mac=%s&uuid=%s&os=installed" % (
            posts.M01["boot-info"]["mac"].replace(":", "-"), posts.M01["boot-info"]["uuid"])
        r = self.app.post("/lifecycle/rolling/%s" % rawq)
        self.assertEqual(200, r.status_code)
        r = self.app.get("/lifecycle/rolling/%s" % rawq)
        self.assertEqual(200, r.status_code)
        self.assertEqual('Enabled 52:54:00:e8:32:5b', r.data)
        r = self.app.post("/lifecycle/rolling/%s" % rawq)
        self.assertEqual(200, r.status_code)

    def test_lifecycle_06(self):
        r = self.app.get("/lifecycle/rolling")
        d = json.loads(r.data)
        self.assertEqual(1, len(d))
        self.assertTrue(d[0]["enable"])

    def test_lifecycle_07(self):
        rawq = "mac=%s&uuid=%s&os=installed" % (
            posts.M02["boot-info"]["mac"].replace(":", "-"), posts.M02["boot-info"]["uuid"])
        r = self.app.get("/lifecycle/rolling/%s" % rawq)
        self.assertEqual(401, r.status_code)
        self.assertEqual('ForeignDisabled 52:54:00:a5:24:f5', r.data)

    def test_vue_machine(self):
        r = self.app.get("/ui/view/machine")
        d = json.loads(r.data)
        self.assertEqual([
            "Created",
            "cidr-boot",
            "mac-boot",
            "fqdn",
            "Roles",
            "Installed",
            "Up-to-date",
            "Rolling"
        ], d[0])
