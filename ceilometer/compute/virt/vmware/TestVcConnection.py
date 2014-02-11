'''
Created on 17-Dec-2013

@author: akhils@vmware.com
'''

from ceilometer.compute.virt.vmware.api import VMwareAPISession
from ceilometer.compute.virt.vmware import vc_perf_stats_util
from ceilometer.openstack.common import gettextutils



if __name__ == '__main__':
    gettextutils.install('ceilometer')
    print 'Testing VC API....'
    api_session = VMwareAPISession("10.112.107.99", "root", "vmware", 0, None, wsdl_loc="https://10.112.107.99/sdk/vimService.wsdl")
    vc_perf_stats_util.query_perf_stats(api_session, 8, "", 300, ["vm-13"], {})()
    print 'Done !!!'
