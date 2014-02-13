'''
Created on 17-Dec-2013

@author: akhils@vmware.com
'''

from ceilometer.compute.virt.vmware.api import VMwareAPISession
from ceilometer.openstack.common import gettextutils
from ceilometer.compute.virt.vmware.vsphere_operations import VsphereOperations

if __name__ == '__main__':
    gettextutils.install('ceilometer')
    wsdl_loc = "https://10.112.107.99/sdk/vimService.wsdl"
    print 'Testing VC API....'
    api_session = VMwareAPISession("10.112.107.120", "root", "vmware",
                                   0, None, wsdl_loc=wsdl_loc)
    # result = vc_perf_stats_util.query_perf_stats(api_session, 6, "", 20,
    #                                             ["vm-72"], {})
    vsphere_ops = VsphereOperations(api_session)
    # result = vsphere_ops.query_realtime_perf_stats("vm-46", 6, True)
    result = vsphere_ops.get_all_vms()
    print 'Done !!!'
