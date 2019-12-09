import os
import re
from avocado import skipIf
from testlib_avocado.timeoutlib import wait
from testlib_avocado.libdisc import Disc
from testlib_avocado.machineslib import MachinesLib
from testlib_avocado.seleniumlib import clickable, invisible, text_in
from selenium.webdriver.common.keys import Keys


class MachinesStoragePoolTestSuite(MachinesLib):
    """
    :avocado: enable
    :avocado: tags=machines
    """

    def testCheckStoragePool(self):
        self.wait_css('#card-pf-storage-pools')
        cmd_active = int(self.machine.execute('virsh pool-list | awk \'NR>=3{if($0!="")print}\' | wc -l')) + int(
            self.machine.execute('sudo virsh pool-list | awk \'NR>=3{if($0!="")print}\' | wc -l'))
        self.wait_css('#card-pf-storage-pools > div > p > span:nth-child(1)', cond=text_in, text_=str(cmd_active))

        active = int(self.wait_css(
            '#card-pf-storage-pools > div > p > span:nth-child(1)').text)
        inactive = int(self.wait_css(
            '#card-pf-storage-pools > div > p > span:nth-child(2)').text)
        total = int(self.wait_css(
            '#card-pf-storage-pools > h2 > button > span.card-pf-aggregate-status-count').text)
        self.assertEqual(total, active + inactive,
                         "Storage pools' total num is not the same as the sum of active and inactive")

        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.wait_css('#storage-pools-listing')

        # iterate groups elements
        page_active = 0
        page_inactive = 0
        group = self.driver.find_elements_by_css_selector(
            '#storage-pools-listing table tbody')
        self.assertEqual(len(group), total)
        for el in group:
            if el.find_element_by_css_selector(
                    'tr > td > span').text == 'active':
                page_active += 1
            elif el.find_element_by_css_selector(
                    'tr > td > span').text == 'inactive':
                page_inactive += 1

        cmd_total = int(self.machine.execute('virsh pool-list --all | wc -l')) - 3 + int(self.machine.execute('sudo virsh pool-list --all | wc -l')) - 3
        self.assertEqual(cmd_total, page_active + page_inactive)

        self.click(self.wait_css('#app div a'))
        self.wait_css('#storage-pools-listing', cond=invisible)
        self.wait_css('#virtual-machines-listing')

    def testCreateDirStoragePool(self):
        name = 'test_storage_pool_' + MachinesLib.random_string()
        path = '/home/test_' + MachinesLib.random_string()
        self.machine.execute('sudo mkdir -p {}'.format(path))

        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.wait_css('#storage-pools-listing')

        pool_name = self.create_storage_by_ui(name=name, target_path=path)
        # Get information from page
        page_res = self.wait_css(
            'tr[data-row-id="' + pool_name + '"] > td:nth-child(4)').text.split('/')
        allocation_from_page = float(page_res[0].strip())
        capacity_from_page = float(page_res[1].split(' ')[1])
        # Get information from command line
        cmd_res = self.machine.execute(
            'sudo virsh pool-info --bytes {}'.format(name))
        allocation_from_cmd = round(float(re.compile(r'Allocation:.*')
                                          .search(cmd_res)
                                          .group(0)
                                          .split(' ')[-1]) / (1024 ** 3),
                                    2)
        capacity_from_cmd = round(float(re.compile(r'Capacity:.*')
                                        .search(cmd_res)
                                        .group(0)
                                        .split(' ')[-1]) / (1024 ** 3),
                                  2)
        # Compare
        self.assertEqual(allocation_from_page, allocation_from_cmd)
        self.assertEqual(capacity_from_page, capacity_from_cmd)

    @skipIf(os.environ.get('NFS') is None,
            'Users should define an environment for NFS location')
    def testCreateNFSStoragePool(self):
        name = 'test_nfs_storage_pool_' + MachinesLib.random_string()
        path = '/home/test_nfs_' + MachinesLib.random_string()
        self.storage_pool['pool'] = name
        self.machine.execute('sudo mkdir -p {}'.format(path))

        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.wait_css('#storage-pools-listing')

        pool_name = self.create_storage_by_ui(name=name,
                                              storage_type='netfs',
                                              target_path=path,
                                              host=os.environ.get('NFS'),
                                              source_path='/home/nfs',
                                              start_up=False)

        page_res = self.wait_css('tr[data-row-id="' + pool_name + '"] > td:nth-child(4)').text.split('/')
        allocation_from_page = float(page_res[0].strip())
        capacity_from_page = float(page_res[1].split(' ')[1])
        cmd_res = self.machine.execute(
            'sudo virsh pool-info --bytes {}'.format(name))
        allocation_from_cmd = round(float(re.compile(r'Allocation:.*')
                                          .search(cmd_res)
                                          .group(0)
                                          .split(' ')[-1]) / (1024 ** 3),
                                    2)
        capacity_from_cmd = round(float(re.compile(r'Capacity:.*')
                                        .search(cmd_res)
                                        .group(0)
                                        .split(' ')[-1]) / (1024 ** 3),
                                  2)

        self.assertEqual(allocation_from_page, allocation_from_cmd)
        self.assertEqual(capacity_from_page, capacity_from_cmd)

    def testAddAllPhysicalDiskDevice(self):
        name = 'pdd_' + MachinesLib.random_string()
        pdd = Disc(self.machine)
        device_suffix = 'test' + MachinesLib.random_string()
        device = pdd.adddisc(device_suffix, '100M')

        # Switch from 'Virtual Machines page' to the 'Storage Pool page',
        # and click the button of storage pool creation to get the type of
        # the physical disk device
        parts = self.get_pdd_format_list()
        for part in parts:
            self.machine.execute(
                'sudo dd if=/dev/zero of={} bs=4K count=1024'.format(device))
            pdd.createparttable(device_suffix,
                                parttable='msdos' if part == 'dos' else part)
            pool_name = self.create_storage_by_ui(name=name,
                                                  storage_type='disk',
                                                  target_path='/media',
                                                  source_path=device,
                                                  parted=part)
            self.click(self.wait_css('#{}-name'.format(pool_name), cond=clickable))
            self.click(self.wait_css('#delete-{}'.format(pool_name), cond=clickable))
            self.click(
                self.wait_xpath(
                    '/html/body/div[2]/div[2]/div/div/div[3]/button[2]',
                    cond=clickable))
            self.wait_css('#{}-name', cond=invisible)

        pdd.clear()

    def testAddISCSIStoragePool(self):
        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.wait_css('#storage-pools-listing')

        disc = Disc(self.machine)
        name = 'iscsi_' + MachinesLib.random_string()
        iscsi_name = disc.addtarget('test' + MachinesLib.random_string(),
                                    '100M')

        # iscsiadm needs sudo privilege, so connection must be 'system'
        self.create_storage_by_ui(name=name,
                                  storage_type='iscsi',
                                  target_path='/dev/disk/by-path',
                                  host='127.0.0.1',
                                  source_path=iscsi_name)

        disc.clear()

    def testCheckStateOfStoragePool(self):
        name = 'test_act_' + MachinesLib.random_string()
        path = '/home/' + name

        self.machine.execute('sudo mkdir -p {}'.format(path))
        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.wait_css('#storage-pools-listing')

        el_id_prefix = self.create_storage_by_ui(name=name, target_path=path)
        self.click(self.wait_css('#{}-name'.format(el_id_prefix),
                                 cond=clickable))

        self.click(self.wait_css('#deactivate-{}'.format(el_id_prefix),
                                 cond=clickable))
        self.wait_css('#{}-state'.format(el_id_prefix),
                      cond=text_in,
                      text_='inactive')
        self.assertEqual('inactive', self.machine.execute(
            'sudo virsh pool-list --all | grep %s | awk \'{print $2}\'' % name).strip())

        self.click(self.wait_css('#activate-{}'.format(el_id_prefix),
                                 cond=clickable))
        self.wait_css('#{}-state'.format(el_id_prefix),
                      cond=text_in,
                      text_='active')
        # After re-activating, the state of storage pool
        # which is got from back-end will be changed to 'running'
        self.assertEqual('active', self.machine.execute(
            'sudo virsh pool-list --all | grep %s | awk \'{print $2}\'' % name).strip())

    def testDeleteStoragePool(self):
        name = 'test_act_' + MachinesLib.random_string()
        path = '/home/' + name
        vol_name = 'test_vol_' + MachinesLib.random_string()
        self.machine.execute('sudo mkdir -p {}'.format(path))
        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.wait_css('#storage-pools-listing')

        # Create an active storage pool,
        # then delete it without deleting volumes in it
        el_id_prefix = self.create_storage_by_ui(name=name, target_path=path)
        self.machine.execute(
            'sudo virsh vol-create-as {} {} 10M'.format(name, vol_name))
        self.click(
            self.wait_css('#{}-name'.format(el_id_prefix), cond=clickable))
        self.click(
            self.wait_css('#delete-{}'.format(el_id_prefix), cond=clickable))
        self.click(
            self.wait_xpath('/html/body/div[2]/div[2]/div/div/div[3]/button[2]',
                            cond=clickable))
        self.wait_css('#{}-name'.format(el_id_prefix), cond=invisible)
        self.machine.execute('sudo test -f {}/{}'.format(path, vol_name))

        # Re-create the storage pool,
        # then delete it without deleting volumes in it
        el_id_prefix = self.create_storage_by_ui(name=name, target_path=path)
        self.click(self.wait_css('#{}-name'.format(el_id_prefix),
                                 cond=clickable))
        self.click(self.wait_css(
            '#delete-{}'.format(el_id_prefix), cond=clickable))
        # make sure the checkbox can be checked
        wait(lambda: not self.wait_css('#storage-pool-delete-volumes').is_selected())
        self.check_box(self.wait_css('#storage-pool-delete-volumes'))
        wait(lambda: self.wait_css('#storage-pool-delete-volumes').is_selected())
        self.click(
            self.wait_xpath('/html/body/div[2]/div[2]/div/div/div[3]/button[2]',
                            cond=clickable))
        self.wait_dialog_disappear()
        self.wait_css('#{}-name'.format(el_id_prefix), cond=invisible)
        self.machine.execute(
            'sudo su -c "! test -f {}/{}"'.format(path, vol_name))

        # Create the pool whose state is inactive, then delete it
        el_id_prefix = self.create_storage(name, path)
        self.click(
            self.wait_css('#{}-name'.format(el_id_prefix), cond=clickable))
        self.click(
            self.wait_css('#delete-{}'.format(el_id_prefix), cond=clickable))
        self.click(
            self.wait_xpath('/html/body/div[2]/div[2]/div/div/div[3]/button[2]',
                            cond=clickable))
        self.wait_css('#{}-name'.format(el_id_prefix), cond=invisible)

    @skipIf(os.environ.get('NFS') is None,
            'need an environment variable whose name is NFS')
    def testDeleteNFSPool(self):
        name = 'test_delete_nfs_pool_' + self.random_string()
        self.storage_pool['pool'] = name

        path = '/home/' + name
        self.machine.execute('sudo mkdir -p {}'.format(path))

        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        el_prefix_id = self.create_storage_by_ui(name=name,
                                                 target_path=path,
                                                 host=os.environ.get('NFS'),
                                                 source_path='/home/nfs',
                                                 storage_type='netfs')
        self.wait_css('#{}-name'.format(el_prefix_id))

        vol_name = 'vol_' + self.random_string()
        vol_path = path + '/' + vol_name

        self.machine.execute('sudo virsh vol-create-as {} {} 100M --format qcow2'.format(name, vol_name))
        self.click(self.wait_css('#{}-name'.format(el_prefix_id)))
        self.click(self.wait_css('#delete-{}'.format(el_prefix_id), cond=clickable))
        self.click(self.wait_css(
            'body > div:nth-child(2) > div.fade.in.modal > div > div > div.modal-footer > button.btn.btn-danger',
            cond=clickable))
        self.wait_css('#{}-name'.format(el_prefix_id), cond=invisible)

        self.create_storage_by_ui(name=name,
                                  target_path=path,
                                  host=os.environ.get('NFS'),
                                  source_path='/home/nfs',
                                  storage_type='netfs')
        self.wait_css('#{}-name'.format(el_prefix_id))
        # verify the volume
        self.machine.execute('test -f {}'.format(vol_path))

        self.click(self.wait_css('#{}-name'.format(el_prefix_id)))
        self.click(self.wait_css('#delete-{}'.format(el_prefix_id), cond=clickable))
        # checkbox needs twice click
        self.send_keys(self.wait_css('#storage-pool-delete-volumes'),
                       Keys.SPACE,
                       clear=False)
        self.click(self.wait_css(
            'body > div:nth-child(2) > div.fade.in.modal > div > div > div.modal-footer > button.btn.btn-danger',
            cond=clickable))
        self.wait_css('#{}-name'.format(el_prefix_id), cond=invisible)

        self.create_storage_by_ui(name=name,
                                  target_path=path,
                                  host=os.environ.get('NFS'),
                                  source_path='/home/nfs',
                                  storage_type='netfs')
        self.wait_css('#{}-name'.format(el_prefix_id))
        self.machine.execute('! test -f {}'.format(vol_path))

    def testDeleteISCSIPool(self):
        pool_name = 'test_iscsi_deletation_' + MachinesLib.random_string()
        disc = Disc(self.machine)
        iscsi_iqn = disc.addtarget(
            'test-' + MachinesLib.random_string(),
            size='100M')

        # Delete active ISCSI Storage Pool
        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                             cond=clickable))
        el_prefix_id = self.create_storage_by_ui(name=pool_name,
                                                 storage_type='iscsi',
                                                 target_path='/dev/disk/by-path',
                                                 host='127.0.0.1',
                                                 source_path=iscsi_iqn)
        self.click(
            self.wait_css('#{}-name'.format(el_prefix_id), cond=clickable))

        self.click(
            self.wait_css('#delete-{}'.format(el_prefix_id), cond=clickable))
        self.click(
            self.wait_css('body > div:nth-child(2) > div.fade.in.modal > div > div > div.modal-footer > button.btn.btn-danger',
                          cond=clickable))
        self.wait_css('#{}-name'.format(el_prefix_id), cond=invisible)

        cmd_res = self.machine.execute(
            'sudo virsh pool-list --all | awk \'NR>=3{if($0!="")print $1}\'')
        self.assertTrue(pool_name not in cmd_res)

        # Delete inactive ISCSI Storage Pool
        el_prefix_id = self.create_storage_by_ui(name=pool_name,
                                                 storage_type='iscsi',
                                                 target_path='/dev/disk/by-path',
                                                 host='127.0.0.1',
                                                 source_path=iscsi_iqn)
        self.click(
            self.wait_css('#{}-name'.format(el_prefix_id), cond=clickable))

        self.click(self.wait_css('#deactivate-{}'.format(el_prefix_id),
                                 cond=clickable))
        self.wait_css('#{}-state'.format(el_prefix_id),
                      cond=text_in,
                      text_='inactive')

        self.click(
            self.wait_css('#delete-{}'.format(el_prefix_id), cond=clickable))
        self.click(
            self.wait_css('body > div:nth-child(2) > div.fade.in.modal > div > div > div.modal-footer > button.btn.btn-danger',
                          cond=clickable))
        self.wait_css('#{}-name'.format(el_prefix_id), cond=invisible)

        cmd_res = self.machine.execute(
            'sudo virsh pool-list --all | awk \'NR>=3{if($0!="")print $1}\'')
        self.assertTrue(pool_name not in cmd_res)

        disc.clear(del_disk=False)

    def testDeletePddPool(self):
        disc = Disc(self.machine)
        device_suffix = 'test' + MachinesLib.random_string()
        device = disc.adddisc(device_suffix, '100M')
        self.machine.execute('sudo dd if=/dev/zero of={} bs=4K count=25600'.format(device))
        disc.createparttable(device_suffix)

        vol_name = device.split('/')[-1] + '1'
        pdd_name = 'test_pdd_deletion_' + MachinesLib.random_string()

        self.click(self.wait_css('#card-pf-storage-pools button',
                                 cond=clickable))
        el_prefix_id = self.create_storage_by_ui(name=pdd_name,
                                                 storage_type='disk',
                                                 target_path='/media',
                                                 source_path=device,
                                                 parted='dos')
        self.click(self.wait_css('#{}-name'.format(el_prefix_id), cond=clickable))
        self.machine.execute('sudo virsh vol-create-as {} {} --capacity {}'.format(pdd_name, vol_name, '10M'))

        self.click(self.wait_css('#delete-{}'.format(el_prefix_id),
                                 cond=clickable))
        self.click(self.wait_css('body > div:nth-child(2) > div.fade.in.modal > div > div > div.modal-footer > button.btn.btn-danger',
                                 cond=clickable))
        self.wait_css('#{}-name'.format(el_prefix_id), cond=invisible)
        wait(lambda:vol_name in self.machine.execute('lsblk'))

        el_prefix_id = self.create_storage_by_ui(name=pdd_name,
                                                 storage_type='disk',
                                                 target_path='/media',
                                                 source_path=device,
                                                 parted='dos')
        self.click(self.wait_css('#{}-name'.format(el_prefix_id), cond=clickable))
        self.click(self.wait_css('#deactivate-{}'.format(el_prefix_id), cond=clickable))
        self.wait_css('#{}-state'.format(el_prefix_id),
                      cond=text_in,
                      text_='inactive')
        self.click(self.wait_css('#delete-{}'.format(el_prefix_id), cond=clickable))
        self.click(self.wait_css('body > div:nth-child(2) > div.fade.in.modal > div > div > div.modal-footer > button.btn.btn-danger',
                                 cond=clickable))
        self.wait_css('#{}-name'.format(el_prefix_id), cond=invisible)
        wait(lambda:vol_name in self.machine.execute('lsblk'))

        el_prefix_id = self.create_storage_by_ui(name=pdd_name,
                                                 storage_type='disk',
                                                 target_path='/media',
                                                 source_path=device,
                                                 parted='dos')
        self.click(self.wait_css('#{}-name'.format(el_prefix_id), cond=clickable))
        self.click(self.wait_css('#delete-{}'.format(el_prefix_id), cond=clickable))
        # make sure the checkbox can be checked
        wait(lambda: not self.wait_css('#storage-pool-delete-volumes').is_selected())
        self.check_box(self.wait_css('#storage-pool-delete-volumes', cond=clickable))
        wait(lambda: self.wait_css('#storage-pool-delete-volumes').is_selected())

        self.click(self.wait_css('body > div:nth-child(2) > div.fade.in.modal > div > div > div.modal-footer > button.btn.btn-danger',
                                 cond=clickable))
        self.wait_css('#{}-name'.format(el_prefix_id), cond=invisible)
        wait(lambda: vol_name not in self.machine.execute('lsblk'))

        disc.clear()

    def testDeleteVolume(self):
        pool_name = 'test' + MachinesLib.random_string()
        pool_path = '/home/{}'.format(pool_name)
        vol_name = 'test_vol_' + MachinesLib.random_string()
        # Create storage pool and volume
        self.machine.execute('sudo mkdir {}'.format(pool_path))
        self.machine.execute('sudo virsh pool-create-as {} {} --target {}'.format(pool_name, 'dir', pool_path))
        self.machine.execute('sudo virsh vol-create-as {} {} {}'.format(pool_name, vol_name, '10M'))
        # Refresh to reload the pool information
        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.refresh_machines_page()
        # Check information about the pool and volume which is created above
        self.click(self.wait_css('#pool-{}-system-name'.format(pool_name), cond=clickable))
        self.click(self.wait_css('#pool-{}-system-storage-volumes'.format(pool_name), cond=clickable))
        self.wait_css('#pool-{}-system-volume-{}-name'.format(pool_name, vol_name), cond=clickable)
        # Delet the volume
        self.wait_css('#storage-volumes-delete', cond=invisible)
        self.check_box(self.wait_css('tr[data-row-id="pool-{}-system"] ~ tr input[name="checkrow0"]'.format(pool_name),
                                     cond=clickable))
        self.wait_css('#storage-volumes-delete',
                      cond=text_in,
                      text_='Delete 1 volume')
        self.click(self.wait_css('#storage-volumes-delete', cond=clickable))
        # Check
        self.wait_css('#pool-{}-system-volume-{}-name'.format(pool_name, vol_name), cond=invisible)
        self.assertNotIn(vol_name,
                         self.machine.execute('ls {}'.format(pool_path)))

    def testCheckVolumeUser(self):
        name = 'staticvm'

        self.create_vm(name)

        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.click(self.wait_css('#pool-default-system-name', cond=clickable))
        self.click(self.wait_css('#pool-default-system-storage-volumes', cond=clickable))
        self.wait_css('#pool-default-system-volume-cirros\.qcow2-usedby', cond=text_in, text_=name)
