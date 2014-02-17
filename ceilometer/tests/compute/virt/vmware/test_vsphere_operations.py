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

from ceilometer.openstack.common import test
from ceilometer.compute.virt.vmware import vsphere_operations
from ceilometer.compute.virt.vmware import api


class VsphereOperationsTest(test.BaseTestCase):

    def setUp(self):
        api_session = api.VMwareAPISession("test_server", "test_user",
                                           "test_password", 0, None,
                                           create_session=False)
        api_session._vim = mock.MagicMock()
        self._vsphere_ops = vsphere_operations.VsphereOperations(api_session)
        super(VsphereOperationsTest, self).setUp()

    def _construct_mock_counter_info(self, group_name, counter_name,
                                     rollup_type, counter_id):
        counter_info = mock.MagicMock()
        counter_info.groupInfo.key = group_name
        counter_info.nameInfo.key = counter_name
        counter_info.rollupType = rollup_type
        counter_info.key = counter_id
        return counter_info

    def test_get_perf_counter_id(self):

        def retrieve_props_side_effect(prop_collector, specSet,
                                                options):
            # assert inputs
            self.assertEquals(vsphere_operations.PERF_COUNTER_PROPERTY,
                              specSet[0].pathSet[0])

            # mock return result
            counter_info1 = self._construct_mock_counter_info("a", "b", "c", 1)
            counter_info2 = self._construct_mock_counter_info("x", "y", "z", 2)
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
