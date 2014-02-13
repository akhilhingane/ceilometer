'''
Created on 17-Dec-2013

@author: akhils@vmware.com
'''

from ceilometer.compute.virt.vmware.api import VMwareAPISession
from ceilometer.openstack.common import gettextutils
from ceilometer.compute.virt.vmware.vc_perf_stats_util import VsphereOperations

if __name__ == '__main__':
    gettextutils.install('ceilometer')
    wsdl_loc = "https://10.112.107.99/sdk/vimService.wsdl"
    print 'Testing VC API....'
    api_session = VMwareAPISession("10.112.107.99", "root", "vmware",
                                   0, None,
                                   wsdl_loc=wsdl_loc)
    # result = vc_perf_stats_util.query_perf_stats(api_session, 6, "", 20,
    #                                             ["vm-72"], {})
    VsphereOperations(api_session)
    # result = vc_perf_stats_util.query_perf_counter_ids(api_session)
    # vc_perf_stats_util.query_perf_counter_ids(api_session._vim)
    print 'Done !!!'
