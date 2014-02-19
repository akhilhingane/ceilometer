# Copyright (c) 2014 VMware, Inc.
# All Rights Reserved.
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

from ceilometer.compute.virt.vmware import vim_util


PERF_MANAGER_TYPE = "PerformanceManager"
PERF_COUNTER_PROPERTY = "perfCounter"
# Time interval of Performance statistics in seconds
REAL_TIME_SAMPLING_INTERVAL = 20


class VsphereOperations(object):
    """Class to invoke vSphere APIs calls required by various
       pollsters, collecting data from VMware infrastructure.
    """
    def __init__(self, api_session, max_objects):
        self._api_session = api_session
        self._max_objects = max_objects
        # Mapping between "VM's Nova instance Id" -> "VM's MOID"
        # In case a VM is deployed by Nova, then its name is instance ID.
        # So this map essentially has VM names as keys.
        self._vm_moid_lookup_map = {}

        # Mapping from full name -> ID, for VC Performance counters
        self._perf_counter_id_lookup_map = None

    def _init_vm_moid_lookup_map(self):
        session = self._api_session
        result = session.invoke_api(vim_util, "get_objects", session.vim,
                                    "VirtualMachine", self._max_objects,
                                    ["name"], False)
        while result:
            for vm_object in result.objects:
                vm_moid = vm_object.obj.value
                vm_name = vm_object.propSet[0].val
                self._vm_moid_lookup_map[vm_name] = vm_moid

            result = session.invoke_api(vim_util, "continue_retrieval",
                                        session.vim, result)

    def get_vm_moid(self, vm_instance_id):
        """Method returns VC MOID of the VM by its NOVA instance ID.
        """
        if vm_instance_id not in self._vm_moid_lookup_map:
            self._init_vm_moid_lookup_map()

        return self._vm_moid_lookup_map.get(vm_instance_id, None)

    def _init_perf_counter_id_lookup_map(self):
        """Method queries the details of various performance counters
        registered with the specified VC and initializes the counter id lookup
        map.
        """

        # Query details of all the performance counters from VC
        session = self._api_session
        client_factory = session.vim.client.factory
        perf_manager = session.vim.service_content.perfManager

        prop_spec = vim_util.build_property_spec(
            client_factory, PERF_MANAGER_TYPE, [PERF_COUNTER_PROPERTY])

        obj_spec = vim_util.build_object_spec(
            client_factory, perf_manager, None)

        filter_spec = vim_util.build_property_filter_spec(
            client_factory, [prop_spec], [obj_spec])

        options = client_factory.create('ns0:RetrieveOptions')
        options.maxObjects = 1

        prop_collector = session.vim.service_content.propertyCollector
        result = session.invoke_api(session.vim, "RetrievePropertiesEx",
                                    prop_collector, specSet=[filter_spec],
                                    options=options)

        perf_counter_infos = result.objects[0].propSet[0].val.PerfCounterInfo

        # Extract the counter Id for each counter and populate the map
        self._perf_counter_id_lookup_map = {}
        for perf_counter_info in perf_counter_infos:

            counter_group = perf_counter_info.groupInfo.key
            counter_name = perf_counter_info.nameInfo.key
            counter_rollup_type = perf_counter_info.rollupType
            counter_id = perf_counter_info.key

            counter_full_name = counter_group + ":" + counter_name + ":" + \
                counter_rollup_type
            self._perf_counter_id_lookup_map[counter_full_name] = counter_id

    def get_perf_counter_id(self, counter_full_name):
        """Method returns the ID of VC performance counter by its full name

        A VC performance counter is uniquely identified by the
        tuple {'Group Name', 'Counter Name', 'Rollup Type'}.
        It will have an id - counter ID (changes from one VC to another),
        which is required to query performance stats from that VC.
        This method returns the ID for a counter,
        assuming 'CounterFullName' => 'Group Name:CounterName:RollupType'

        :param counter_full_name
        """
        if not self._perf_counter_id_lookup_map:
            self._init_perf_counter_id_lookup_map()
        return self._perf_counter_id_lookup_map[counter_full_name]

    # TODO(akhils@vmware.com) Move this method to common library
    # when it gets checked-in
    def query_vm_property(self, vm_moid, property_name):
        """Method returns the value of specified property for a VM

        :param vm_moid: moid of the VM whose property is to be queried
        :param property_name: path of the property
        """
        vm_mobj = vim_util.get_moref(vm_moid, "VirtualMachine")
        session = self._api_session
        return session.invoke_api(vim_util, "get_object_property",
                                  session.vim, vm_mobj, property_name)

    def query_vm_current_stat_value(self, vm_moid, counter_id,
                                    is_counter_aggregate):
        """Method returns the current value of the specified perf stat counter
        for a VM.

        :param vm_moid: moid of the VM for which stats are needed
        :param counter_id: id of the perf counter in VC
        :param is_counter_aggregate: whether the counter is 'aggregate'
               or 'instance'
        """

        session = self._api_session
        client_factory = session.vim.client.factory

        # Construct the QuerySpec
        metric_id = client_factory.create('ns0:PerfMetricId')
        metric_id.counterId = counter_id
        if is_counter_aggregate:
            metric_id.instance = ""
        else:
            metric_id.instance = "*"

        query_spec = client_factory.create('ns0:PerfQuerySpec')
        query_spec.entity = vim_util.get_moref(vm_moid, "VirtualMachine")
        query_spec.metricId = [metric_id]
        query_spec.intervalId = REAL_TIME_SAMPLING_INTERVAL
        # [TODO(akhils@vmware.com):]query_spec.startTime = from_time

        perf_manager = session.vim.service_content.perfManager
        perf_stats = session.invoke_api(session.vim, 'QueryPerf', perf_manager,
                                        querySpec=[query_spec])

        stat_val = 0
        if not perf_stats:
            return stat_val

        entity_metric = perf_stats[0]
        sample_infos = entity_metric.sampleInfo
        samples_count = len(sample_infos)

        for metric_series in entity_metric.value:
            stat_val += metric_series.value[samples_count - 1]

        return stat_val
