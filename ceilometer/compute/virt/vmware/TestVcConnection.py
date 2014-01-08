'''
Created on 17-Dec-2013

@author: akhils@vmware.com
'''

from ceilometer.compute.virt.vmware.api import VMwareAPISession
from ceilometer.compute.virt.vmware import vc_perf_stats_util



if __name__ == '__main__':

    api_session = VMwareAPISession("10.112.107.99", "root", "vmware", 0, 0, wsdl_loc="https://10.112.107.99/sdk/vimService.wsdl")
    vc_perf_stats_util.query_perf_counter_ids(api_session._vim)
    print 'Done !!!'
