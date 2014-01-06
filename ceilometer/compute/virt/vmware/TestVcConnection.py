'''
Created on 17-Dec-2013

@author: akhils@vmware.com
'''

from ceilometer.compute.virt.vmware import vim_util
from ceilometer.compute.virt.vmware.api import VMwareAPISession

def query_perf_counter_info(vim):
    perf_manager_type = "PerformanceManager"
    perf_counter_property = "perfCounter"
    client_factory = vim.client.factory
    
    prop_spec = vim_util.build_property_spec(client_factory, perf_manager_type, [perf_counter_property])
    obj_spec = vim_util.build_object_spec(client_factory, vim.service_content.perfManager, None)
    filter_spec = vim_util.build_property_filter_spec(client_factory, [prop_spec], [obj_spec])
    
    options = client_factory.create('ns0:RetrieveOptions')
    options.maxObjects = 1
    result = vim.RetrievePropertiesEx(vim.service_content.propertyCollector, specSet=[filter_spec], options=options)
    perfCounterInfos = result.objects[0].propSet[0].val.PerfCounterInfo
    for perfCounterInfo in perfCounterInfos:
        counterGroup = perfCounterInfo.groupInfo.key
        counterName = perfCounterInfo.nameInfo.key
        counterRollupType = perfCounterInfo.rollupType
        counterId = perfCounterInfo.key
        counterIdStr = counterGroup + "." + counterName + "." + counterRollupType
        print "%d: %s" % (counterId, counterIdStr)
    
    print "Retrieved properties"

if __name__ == '__main__':
    
    api_session = VMwareAPISession("10.112.107.99", "root", "vmware", 0, 0, wsdl_loc="https://10.112.107.99/sdk/vimService.wsdl")
    # api_session._vim._service_content.
    query_perf_counter_info(api_session._vim)
    print 'Done !!!'
