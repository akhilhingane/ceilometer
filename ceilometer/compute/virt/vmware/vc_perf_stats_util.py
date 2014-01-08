"""
@author: akhils@vmware.com
"""

from ceilometer.compute.virt.vmware import vim_util

PERF_MANAGER_TYPE = "performanceManager"
PERF_COUNTER_PROPERTY = "perfCounter"
def query_perf_counter_ids(vim):

    """
    Method queries the details of various performance counters registered with the specified VC.
    A VC performance counter is uniquely identified by the tuple {'Group Name', 'Counter Name', 'Rollup Type'}.
    It will have an integer id - counter ID (changes from one VC to another) which is required to query
    performance stats from that VC. 
    This method aims at finding the counter IDs for various counters.
    
    The return type is a multilevel map:
        'Group Name' -> 'Counter Name' -> 'Rollup Type' -> 'Counter ID'.
        
    """
    
    # Query details of all the performance counters from VC
    client_factory = vim.client.factory
    
    prop_spec = vim_util.build_property_spec(client_factory, PERF_MANAGER_TYPE, [PERF_COUNTER_PROPERTY])
    obj_spec = vim_util.build_object_spec(client_factory, vim.service_content.perfManager, None)
    filter_spec = vim_util.build_property_filter_spec(client_factory, [prop_spec], [obj_spec])    
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = 1
    
    result = vim.RetrievePropertiesEx(vim.service_content.propertyCollector, specSet=[filter_spec], options=options)
    perf_counter_infos = result.objects[0].propSet[0].val.PerfCounterInfo

    # Extract the counter Id for each counter and populate the return map
    perf_counter_id_map = {}    
    for perf_counter_info in perf_counter_infos:
        
        counter_group = perf_counter_info.groupInfo.key
        counter_name = perf_counter_info.nameInfo.key
        counter_rollup_type = perf_counter_info.rollupType
        counter_id = perf_counter_info.key
        
        if not perf_counter_id_map.has_key(counter_group) :
            perf_counter_id_map[counter_group] = {}
        name_map = perf_counter_id_map[counter_group]
        
        if not name_map.has_key(counter_name) :
            name_map[counter_name] = {}
        rollup_type_to_id_map = name_map[counter_name]
        
        rollup_type_to_id_map[counter_rollup_type] = counter_id         

    return perf_counter_id_map

def query_perf_stats(vim, counter_id, instance_id, sample_interval, entity_moids, entity_start_times):
    """
    :param vim: Vim object used to execute VC queries
    :param counter_id: id of the perf counter in VC
    :param instance_id: instance for which stats are to be queried. 
                If stats are required for all instances then pass 
                (a) empty string ("") for aggregate counters
                (b) asterisk ("*") for instance counters
    :param sample_interval: interval of the stats in seconds
    :param entity_moids: list of moids of entities for whom stats are needed
    :param entity_start_times: for each entity this map should contain the time 
                from which stats are needed for that entity. 
                End time is not restricted and hence stats till current time are returned.
    """
    # Construct the QuerySpec
    # metricId = 
    # query_specs = []
    # perfMgr = vim.service_content.perfManager
    # perfMgr.queryStats();
    