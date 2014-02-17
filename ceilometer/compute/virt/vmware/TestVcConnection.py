# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

'''
Created on 17-Dec-2013

@author: akhils@vmware.com
'''

from ceilometer.compute.virt.vmware.api import VMwareAPISession
from ceilometer.compute.virt.vmware.vsphere_operations import VsphereOperations
from ceilometer.openstack.common import gettextutils


if __name__ == '__main__':
    gettextutils.install('ceilometer')
    wsdl_loc = "https://10.112.107.120/sdk/vimService.wsdl"
    print('Testing VC API....')
    api_session = VMwareAPISession("10.112.107.120", "root", "vmware",
                                   0, None, wsdl_loc=wsdl_loc)
    # vm-21
    # result = vc_perf_stats_util.query_perf_stats(api_session, 6, "", 20,
    #                                             ["vm-72"], {})
    vsphere_ops = VsphereOperations(api_session)
    result = vsphere_ops.get_perf_counter_id("cpu:usagemhz:average")
    result = vsphere_ops.get_vm_moid("DEV-VC-5.5")
    result = vsphere_ops.query_vm_property("vm-21", "config.annotation")
    result = vsphere_ops.query_vm_current_stat_value("vm-21", 6, True)
    print('Done !!!')
