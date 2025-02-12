import unittest
import requests
import sys
import json
import subprocess
import sys
import os
import yaml
import time

class TestKubePlus(unittest.TestCase):

    @classmethod
    def run_command(self, cmd):
        #print(cmd)
        cmdOut = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        out = cmdOut[0].decode('utf-8')
        err = cmdOut[1].decode('utf-8')
        #print(out)
        #print("---")
        #print(err)
        return out, err

    @classmethod
    def _is_kubeplus_running(self):
        cmd = 'kubectl get pods -A'
        out, err = TestKubePlus.run_command(cmd)
        for line in out.split("\n"):
            if 'kubeplus' in line and 'Running' in line:
                return True
        return False

    @classmethod
    def _is_kyverno_running(self):
        cmd = 'kubectl get pods -A'
        out, err = TestKubePlus.run_command(cmd)
        for line in out.split("\n"):
            if 'kyverno' in line and 'Running' in line:
                return True
        return False

    def test_create_res_comp_for_chart_with_ns(self):
        if not TestKubePlus._is_kubeplus_running():
            print("KubePlus is not running. Deploy KubePlus and then run tests")
            sys.exit(0)

        cmd = "kubectl create -f wordpress-service-composition-chart-withns.yaml --kubeconfig=../kubeplus-saas-provider.json"
        out, err = TestKubePlus.run_command(cmd)
        #print("Out:" + out)
        #print("Err:" + err)
        self.assertTrue('Namespace object is not allowed in the chart' in err)

    def test_create_res_comp_for_chart_with_shared_storage(self):
        if not TestKubePlus._is_kubeplus_running():
            print("KubePlus is not running. Deploy KubePlus and then run tests")
            sys.exit(0)

        cmd = "kubectl create -f storage-class-fast.yaml"
        TestKubePlus.run_command(cmd)

        cmd = "kubectl create -f storage-isolation/wordpress-service-composition.yaml --kubeconfig=../kubeplus-saas-provider.json"
        out, err = TestKubePlus.run_command(cmd)
        #print("Out:" + out)
        #print("Err:" + err)
        self.assertTrue('Storage class with reclaim policy Retain not allowed' in err)

        cmd = "kubectl delete -f storage-class-fast.yaml"
        TestKubePlus.run_command(cmd)

    def test_create_res_comp_with_incomplete_resource_quota(self):
        if not TestKubePlus._is_kubeplus_running():
            print("KubePlus is not running. Deploy KubePlus and then run tests")
            sys.exit(0)

        cmd = "kubectl create -f resource-quota/wordpress-service-composition-1.yaml --kubeconfig=../kubeplus-saas-provider.json"
        out, err = TestKubePlus.run_command(cmd)
        #print("Out:" + out)
        #print("Err:" + err)
        self.assertTrue('If quota is specified, specify all four values: requests.cpu, requests.memory, limits.cpu, limits.memory' in err)

    def test_res_comp_with_no_podpolicies(self):
        if not TestKubePlus._is_kubeplus_running():
            print("KubePlus is not running. Deploy KubePlus and then run tests")
            sys.exit(0)

        cmd = "kubectl create -f wordpress-service-composition-chart-nopodpolicies.yaml --kubeconfig=../kubeplus-saas-provider.json"
        TestKubePlus.run_command(cmd)

        installed = False
        cmd = "kubectl get crds"
        timer = 0
        while not installed and timer < 30:
            out, err = TestKubePlus.run_command(cmd)
            if 'wordpressservices.platformapi.kubeplus' in out:
                installed = True
            else:
                time.sleep(1)
                timer = timer + 1

        cmd = "kubectl create -f tenant1.yaml --kubeconfig=../kubeplus-saas-provider.json"
        TestKubePlus.run_command(cmd)

        all_running = False
        cmd = "kubectl get pods -n wp-for-tenant1"
        pods = []
        timer = 0
        while not all_running and timer < 30:
            timer = timer + 1
            out, err = TestKubePlus.run_command(cmd)
            count = 0
            for line in out.split("\n"):
                if 'Running' in line:
                    count = count + 1
                if 'NAME' not in line:
                    parts = line.split(" ")
                    pod = parts[0].strip()
                    if pod != '' and pod not in pods:
                        pods.append(pod)
            if count == 2:
                all_running = True

        if count < 2:
            print("Application Pod not started..")
        else:
            #print(pods)
            # Check container configs
            for pod in pods:
                cmd = "kubectl get pod " + pod + " -n wp-for-tenant1 -o json "
                out, err = TestKubePlus.run_command(cmd)
                json_obj = json.loads(out)
                #print(json_obj)
                #print(json_obj['spec']['containers'][0])
                resources = json_obj['spec']['containers'][0]['resources']
                if not resources:
                    self.assertTrue(True)
                else:
                    self.assertTrue(False)

        #clean up
        cmd = "kubectl delete -f tenant1.yaml --kubeconfig=../kubeplus-saas-provider.json"
        TestKubePlus.run_command(cmd)

        cmd = "kubectl delete -f wordpress-service-composition-chart-nopodpolicies.yaml --kubeconfig=../kubeplus-saas-provider.json"
        TestKubePlus.run_command(cmd)

        removed = False
        cmd = "kubectl get crds"
        timer = 0
        while not removed and timer < 60:
            timer = timer + 1
            out, err = TestKubePlus.run_command(cmd)
            if 'wordpressservices.platformapi.kubeplus' not in out:
                removed = True
            else:
                time.sleep(1)

    # TODO: Add tests for
    # kubectl connections
    # kubectl appresources
    # kubectl appurl
    # kubectl applogs
    # kubectl metrics
    @unittest.skip("Skipping CLI test")
    def test_kubeplus_cli(self):
        kubeplus_home = os.getenv("KUBEPLUS_HOME")
        print("KubePlus home:" + kubeplus_home)
        path = os.getenv("PATH")
        print("Path:" + path)

        instance = ""
        kind = "wp"
        ns = "default"
        kubeplus_saas_provider = kubeplus_home + "/kubeplus-saas-provider.json"
        cmdsuffix = kind + " " + instance + " " + ns + " -k " + kubeplus_saas_provider 
        cmd = "kubectl connections " + cmdsuffix

    @unittest.skip("Skipping Kyverno integration test")
    def test_kyverno_policies(self):
        if not TestKubePlus._is_kubeplus_running():
            print("KubePlus is not running. Deploy KubePlus and then run tests")
            sys.exit(0)

        if not TestKubePlus._is_kyverno_running():
            print("Kyverno is not running. Deploy Kyverno and then run this test.")
            sys.exit(0)

        cmd = "kubectl create -f block-stale-images.yaml"
        TestKubePlus.run_command(cmd)

        cmd = "kubectl create -f resource-quota/wordpress-service-composition.yaml --kubeconfig=../kubeplus-saas-provider.json"
        out, err = TestKubePlus.run_command(cmd)
        #print("Out:" + out)
        #print("Err:" + err)

        for line in err.split("\n"):
            if 'block-stale-images' in line.strip():
                self.assertTrue(True)
                cmd = "kubectl delete -f block-stale-images.yaml"
                TestKubePlus.run_command(cmd)
                return
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
    
