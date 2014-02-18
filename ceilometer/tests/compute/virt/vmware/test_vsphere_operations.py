# Copyright (c) 2014 VMware, Inc.
# All Rights Reserved.
#
#    Author: Akhil Hingane <akhils@vmware.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from ceilometer.compute.virt.vmware import api
from ceilometer.compute.virt.vmware import vsphere_operations
from ceilometer.openstack.common import test


class VsphereOperationsTest(test.BaseTestCase):

    def setUp(self):
        api_session = api.VMwareAPISession("test_server", "test_user",
                                           "test_password", 0, None,
                                           create_session=False)
        api_session._vim = mock.MagicMock()
        self._vsphere_ops = vsphere_operations.VsphereOperations(api_session)
        super(VsphereOperationsTest, self).setUp()

    def test_query_vm_property(self):

        vm_moid = "vm-21"
        vm_property_name = "runtime.powerState"
        vm_property_val = "poweredON"

        def retrieve_props_side_effect(pc, specSet, options):
            # assert inputs
            self.assertEqual(vm_moid, specSet[0].obj.value)
            self.assertEqual(vm_property_name, specSet[0].pathSet[0])

            # mock return result
            result = mock.MagicMock()
            result.objects[0].propSet[0].val = vm_property_val
            return result

        vim_mock = self._vsphere_ops._api_session._vim
        vim_mock.RetrievePropertiesEx.side_effect = retrieve_props_side_effect

        actual_val = self._vsphere_ops.query_vm_property(vm_moid,
                                                         vm_property_name)
        self.assertEqual(vm_property_val, actual_val)

    def test_get_perf_counter_id(self):

        def construct_mock_counter_info(group_name, counter_name, rollup_type,
                                        counter_id):
            counter_info = mock.MagicMock()
            counter_info.groupInfo.key = group_name
            counter_info.nameInfo.key = counter_name
            counter_info.rollupType = rollup_type
            counter_info.key = counter_id
            return counter_info

        def retrieve_props_side_effect(pc, specSet, options):
            # assert inputs
            self.assertEqual(vsphere_operations.PERF_COUNTER_PROPERTY,
                             specSet[0].pathSet[0])

            # mock return result
            counter_info1 = construct_mock_counter_info("a", "b", "c", 1)
            counter_info2 = construct_mock_counter_info("x", "y", "z", 2)
            result = mock.MagicMock()
            result.objects[0].propSet[0].val.PerfCounterInfo.__iter__. \
                return_value = [counter_info1, counter_info2]
            return result

        vim_mock = self._vsphere_ops._api_session._vim
        vim_mock.RetrievePropertiesEx.side_effect = retrieve_props_side_effect

        counter_id = self._vsphere_ops.get_perf_counter_id("a:b:c")
        self.assertEqual(1, counter_id)

        counter_id = self._vsphere_ops.get_perf_counter_id("x:y:z")
        self.assertEqual(2, counter_id)

    def test_query_vm_current_stat_value(self):

        vm_moid = "vm-21"
        counter_id = 5

        def vim_query_perf_side_effect(perf_manager, querySpec):
            # assert inputs
            self.assertEqual(vm_moid, querySpec[0].entity.value)
            self.assertEqual(counter_id, querySpec[0].metricId[0].counterId)
            self.assertEqual(vsphere_operations.REAL_TIME_SAMPLING_INTERVAL,
                             querySpec[0].intervalId)

            # mock return result
            metric_series1 = mock.MagicMock()
            metric_series1.value = [111, 222, 333]

            perf_stats = mock.MagicMock()
            perf_stats[0].sampleInfo = ["s1", "s2", "s3"]
            perf_stats[0].value.__iter__.return_value = [metric_series1]
            return perf_stats

        vim_mock = self._vsphere_ops._api_session._vim
        vim_mock.QueryPerf.side_effect = vim_query_perf_side_effect
        stat_val = self._vsphere_ops.query_vm_current_stat_value(vm_moid,
                                                                 counter_id,
                                                                 True)
        self.assertEqual(333, stat_val)
