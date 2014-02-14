"""
@author: akhils@vmware.com
"""

from ceilometer.compute.virt.vmware import vim_util
from ceilometer.compute.virt.vmware.vim import get_moref

PERF_MANAGER_TYPE = "PerformanceManager"
PERF_COUNTER_PROPERTY = "perfCounter"
REAL_TIME_SAMPLING_INTERVAL = 20  # in seconds
MAX_OBJECTS = 1000


class VsphereOperations(object):

    def __init__(self, api_session):
        self._api_session = api_session
        # Mapping between "VM's nova instance Id" -> "VM's vSphere MOID"
        self.vm_moid_lookup_map = {}

    def _refresh_vm_moid_lookup_map(self):
        vim = self._api_session._vim

        result = vim_util.get_objects(vim, 'VirtualMachine',
                          MAX_OBJECTS, ["name"], False)
        while result:

            for vm_object in result.objects:
                vm_moid = vm_object.obj.value
                vm_name = vm_object.propSet[0].val
                self.vm_moid_lookup_map[vm_name] = vm_moid

            result = vim_util.continue_retrieval(vim, result)

    def get_vm_moid(self, vm_instance_id):
        """
        Method returns VC MOID of the VM by its NOVA instance ID
        """
        if vm_instance_id not in self.vm_moid_lookup_map:
            self._refresh_vm_moid_lookup_map()

        if vm_instance_id in self.vm_moid_lookup_map:
            return self.vm_moid_lookup_map[vm_instance_id]
        else:
            return None

    def query_perf_counter_ids(self):
        """
        Method queries the details of various performance counters registered
        with the specified VC.
        A VC performance counter is uniquely identified by the
        tuple {'Group Name', 'Counter Name', 'Rollup Type'}.
        It will have an id - counter ID (changes from one VC to another)
        which is required to query performance stats from that VC.
        This method aims at finding the counter IDs for various counters.

        Let 'CounterFullName' be 'Group Name:Counter Name:Rollup Type'
        The return type is a map from 'CounterFullName' -> 'Counter ID'.
        """

        # Query details of all the performance counters from VC
        vim = self._api_session._vim
        client_factory = vim.client.factory
        perf_manager = vim.service_content.perfManager

        prop_spec = vim_util.build_property_spec(
            client_factory, PERF_MANAGER_TYPE, [PERF_COUNTER_PROPERTY]
            )

        obj_spec = vim_util.build_object_spec(
            client_factory, perf_manager, None
            )

        filter_spec = vim_util.build_property_filter_spec(
            client_factory, [prop_spec], [obj_spec]
            )

        options = client_factory.create('ns0:RetrieveOptions')
        options.maxObjects = 1

        prop_collector = vim.service_content.propertyCollector
        result = vim.RetrievePropertiesEx(
            prop_collector, specSet=[filter_spec], options=options
            )

        perf_counter_infos = result.objects[0].propSet[0].val.PerfCounterInfo

        # Extract the counter Id for each counter and populate the return map
        perf_counter_full_name_to_id = {}
        for perf_counter_info in perf_counter_infos:

            counter_group = perf_counter_info.groupInfo.key
            counter_name = perf_counter_info.nameInfo.key
            counter_rollup_type = perf_counter_info.rollupType
            counter_id = perf_counter_info.key

            counter_full_name = counter_group + ":" + counter_name + ":" + \
                counter_rollup_type
            perf_counter_full_name_to_id[counter_full_name] = counter_id

        return perf_counter_full_name_to_id

    def query_realtime_perf_stats(self, entity_moid, counter_id,
                                   is_counter_aggregate):
        """
        :param entity_moid: moid of the entity for which stats are needed
        :param counter_id: id of the perf counter in VC
        :param is_counter_aggregate: whether the counter is 'aggregate'
               or 'instance'
        """

        client_factory = self._api_session._vim.client.factory

        # Construct the QuerySpec
        metric_id = client_factory.create('ns0:PerfMetricId')
        metric_id.counterId = counter_id
        if is_counter_aggregate:
            metric_id.instance = ""
        else:
            metric_id.instance = "*"

        query_spec = client_factory.create('ns0:PerfQuerySpec')
        query_spec.entity = get_moref(entity_moid, "VirtualMachine")
        query_spec.metricId = [metric_id]
        query_spec.intervalId = REAL_TIME_SAMPLING_INTERVAL
        # [TODO:]query_spec.startTime = from_time

        perf_manager = self._api_session._vim.service_content.perfManager
        perf_stats = self._api_session.invoke_api(self._api_session._vim,
                    'QueryPerf', perf_manager, querySpec=[query_spec])

        entity_metric = perf_stats[0]
        sample_infos = entity_metric.sampleInfo
        samples_count = len(sample_infos)
        # return the latest sample value
        return entity_metric.value[0].value[samples_count - 1]
