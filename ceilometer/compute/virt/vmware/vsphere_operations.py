"""
@author: akhils@vmware.com
"""

from ceilometer.compute.virt.vmware import vim_util
from ceilometer.compute.virt.vmware.vim import get_moref

PERF_MANAGER_TYPE = "PerformanceManager"
PERF_COUNTER_PROPERTY = "perfCounter"
REAL_TIME_SAMPLING_INTERVAL = 20  # in seconds


class VsphereOperations(object):

    def __init__(self, api_session):
        self._api_session = api_session

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
        perfManager = vim.service_content.perfManager

        prop_spec = vim_util.build_property_spec(
                                                 client_factory,
                                                 PERF_MANAGER_TYPE,
                                                 [PERF_COUNTER_PROPERTY])

        obj_spec = vim_util.build_object_spec(client_factory,
                                              perfManager, None)

        filter_spec = vim_util.build_property_filter_spec(
                                                          client_factory,
                                                          [prop_spec],
                                                          [obj_spec])

        options = client_factory.create('ns0:RetrieveOptions')
        options.maxObjects = 1

        result = vim.RetrievePropertiesEx(
                     vim.service_content.propertyCollector,
                     specSet=[filter_spec], options=options)

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
        :param api_session: used to execute VC queries
        :param counter_id: id of the perf counter in VC
        :param instance_id: instance for which stats are to be queried.
                    If stats are required for all instances then pass
                    (a) empty string ("") for aggregate counters
                    (b) asterisk ("*") for instance counters
        :param sample_interval: interval of the stats in seconds
        :param entity_moid: moid of the entity for which stats are needed
        :param from_time: the time from which the stats need to be queried
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

        perfMgr = self._api_session._vim.service_content.perfManager
        return self._api_session.invoke_api(self._api_session._vim,
                    'QueryPerf', perfMgr, querySpec=[query_spec])
