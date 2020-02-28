from testlib_avocado.seleniumlib import clickable, invisible, text_in
from testlib_avocado.machineslib import MachinesLib
from testlib_avocado.libdisc import Disc


class MachinesDisksTestSuite(MachinesLib):
    """
    :avocado: enable
    :avocado: tags=machines
    """

    def testDiskInfo(self):
        name = "staticvm"
        args = self.create_vm(name)

        self.click(self.wait_css('#vm-{}-disks'.format(name), cond=clickable))
        self.wait_css('#vm-{}-disks-hda-device'.format(name), cond=text_in, text_='disk')
        self.wait_css('#vm-{}-disks-hda-bus'.format(name), cond=text_in, text_='ide')
        self.wait_css('#vm-{}-disks-hda-source-file'.format(name),
                      cond=text_in, text_='{}'.format(args.get('image')))
        self.wait_css('#vm-{}-disks-hda-used'.format(name), cond=text_in, text_='0.02')
        self.wait_css('#vm-{}-disks-hda-capacity'.format(name), cond=text_in, text_='0.04')

    def testAddDiskWithVmOff(self):
        name = "staticvm"
        self.create_vm(name, state='shut off')
        pool = self.prepare_disk('test')

        self.click(self.wait_css('#vm-{}-disks'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-select-pool'.format(name)), pool[1])
        self.send_keys(self.wait_css('#vm-{}-disks-adddisk-new-name'.format(name)), 'qcow2disk_' + MachinesLib.random_string())
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name), cond=clickable))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vda-device'.format(name))

        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-select-pool'.format(name)), pool[2])
        self.send_keys(self.wait_css('#vm-{}-disks-adddisk-new-name'.format(name)), 'raw2disk_' + MachinesLib.random_string())
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-format'.format(name)), 'raw')
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name), cond=clickable))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vdb-device'.format(name))

        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk-useexisting'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-existing-select-pool'.format(name)), pool[1])
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name, cond=clickable)))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vdc-device'.format(name))

        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk-useexisting'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-existing-select-pool'.format(name)), pool[2])
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-existing-select-volume'.format(name)), pool[0][pool[2]][1])
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name, cond=clickable)))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vdd-device'.format(name))

        self.click(self.wait_css('#vm-{}-run'.format(name), cond=clickable))
        self.wait_css('#vm-{}-run'.format(name), cond=invisible)

        self.assertEqual(self.machine.execute("sudo virsh list --all | grep staticvm | awk '{print $3}' ORS=''"), 'running')
        self.assertEqual(self.machine.execute(
            'sudo virsh domblklist ' + name + ' | awk \'NR>=3{if($0!="")print}\' | wc -l').strip(), '5')

    def testAddDiskWithVmOn(self):
        name = "staticvm"
        self.create_vm(name, wait=True)
        pool = self.prepare_disk('test')

        self.click(self.wait_css('#vm-{}-disks'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-select-pool'.format(name)), pool[2])
        self.send_keys(self.wait_css('#vm-{}-disks-adddisk-new-name'.format(name)), 'qcow2disk_' + MachinesLib.random_string())
        self.check_box(self.wait_css('#vm-{}-disks-adddisk-permanent'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name), cond=clickable))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vda-device'.format(name))

        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-select-pool'.format(name)), pool[1])
        self.send_keys(self.wait_css('#vm-{}-disks-adddisk-new-name'.format(name)), 'raw2disk_' + MachinesLib.random_string())
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-format'.format(name)), 'raw')
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name), cond=clickable))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vdb-device'.format(name))

        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk-useexisting'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-existing-select-pool'.format(name)), pool[1])
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name, cond=clickable)))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vdc-device'.format(name))

        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk-useexisting'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-existing-select-pool'.format(name)), pool[2])
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-existing-select-volume'.format(name)), pool[0][pool[2]][1])
        self.check_box(self.wait_css('#vm-{}-disks-adddisk-permanent'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name, cond=clickable)))
        self.wait_dialog_disappear()
        self.wait_css('#vm-{}-disks-vdd-device'.format(name))

        self.click(self.wait_css('#vm-{}-off'.format(name), cond=clickable))
        self.wait_css('#vm-{}-off'.format(name), cond=invisible)

        self.assertEqual(self.machine.execute("sudo virsh list --all | grep " + name + " | awk '{print $3}' ORS=''"), 'shut')
        self.assertEqual(self.machine.execute(
            'sudo virsh domblklist ' + name + ' | awk \'NR>=3{if($0!="")print}\' | wc -l').strip(), '3')

    def testDetachDiskVmOn(self):
        name = "staticvm"
        self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-disks'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-select-pool'.format(name)), 'default')
        self.send_keys(self.wait_css('#vm-{}-disks-adddisk-new-name'.format(name)), 'detachdisk_vm_on_' + MachinesLib.random_string())
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name), cond=clickable))
        self.wait_css('#vm-{}-disks-vda-device'.format(name))
        self.click(self.wait_css('#delete-{}-disk-vda'.format(name), cond=clickable))
        self.click(self.wait_css('.modal-footer button.btn-danger'.format(name), cond=clickable))
        self.wait_css('vm-{}-disks-vda-device'.format(name), cond=invisible)
        self.click(self.wait_css('#vm-{}-off'.format(name), cond=clickable))
        self.wait_css('#vm-{}-off'.format(name), cond=invisible)
        self.click(self.wait_css('#vm-{}-run'.format(name), cond=clickable))
        self.wait_css('#vm-{}-run'.format(name), cond=invisible)
        self.wait_css('#vm-{}-disks-vda-device'.format(name), cond=invisible)

        self.assertEqual(self.machine.execute('sudo virsh domblklist ' + name + ' | awk \'NR>=3{if($0!="")print}\' | wc -l').strip(), '1')

    def testDetachDiskVmOff(self):
        name = "staticvm"
        self.create_vm(name, state='shut off')

        self.click(self.wait_css('#vm-{}-disks'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name), cond=clickable))
        self.select_by_value(self.wait_css('#vm-{}-disks-adddisk-new-select-pool'.format(name)), 'default')
        self.send_keys(self.wait_css('#vm-{}-disks-adddisk-new-name'.format(name)), 'detachdisk_vm_off_' + MachinesLib.random_string())
        self.click(self.wait_css('#vm-{}-disks-adddisk-dialog-add'.format(name), cond=clickable))
        self.wait_css('#vm-{}-disks-vda-device'.format(name))
        self.click(self.wait_css('#delete-{}-disk-vda'.format(name), cond=clickable))
        self.click(self.wait_css('.modal-footer button.btn-danger'.format(name), cond=clickable))
        self.wait_css('#vm-{}-disks-vda-device'.format(name), cond=invisible)
        self.click(self.wait_css('#vm-{}-run'.format(name), cond=clickable))
        self.wait_css('#vm-{}-run'.format(name), cond=invisible)
        self.wait_css('#vm-{}-disks-vda-device'.format(name), cond=invisible)

        self.assertEqual(self.machine.execute('sudo virsh domblklist ' + name + ' | awk \'NR>=3{if($0!="")print}\' | wc -l').strip(), '1')

    def testAddDiskWithPerformanceOption(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name)
        self.click(self.wait_css('#vm-{}-disks'.format(name),
                                 cond=clickable))
        disk_type_l = ['qcow2', 'raw']
        disk_preform_l = ['default',
                          'none',
                          'writethrough',
                          'writeback',
                          'directsync',
                          'unsafe']
        # 'a' in UNICODE
        target_start = 97
        for dt in disk_type_l:
            for dp in disk_preform_l:
                vol = 'vol_' + MachinesLib.random_string()
                self.click(self.wait_css('#vm-{}-disks-adddisk'.format(name),
                                         cond=clickable))
                self.create_disk_by_ui(name,
                                       vol,
                                       size_unit='MiB',
                                       disk_format=dt,
                                       performance=True,
                                       cache_mode=dp)
                self.wait_css('#vm-{}-disks-vd{}-source-volume'.format(name, chr(target_start)),
                              cond=text_in,
                              text_=vol)
                if dp == 'default':
                    self.wait_css('#vm-{}-disks-vd{}-cache'.format(name, chr(target_start)),
                                  cond=invisible)
                else:
                    self.wait_css('#vm-{}-disks-vd{}-cache'.format(name, chr(target_start)),
                                  cond=text_in,
                                  text_=dp)
                self.assertIn(vol, self.machine.execute('sudo virsh dumpxml {}'.format(name)))
                target_start += 1

    def testAddDiskFromISCSIPool(self):
        vm_name = 'test_' + MachinesLib.random_string()
        pool_name = 'test_nfs_' + MachinesLib.random_string()
        disc = Disc(self.machine)
        iqn = disc.addtarget('test' + MachinesLib.random_string(),
                             '100M')

        self.click(self.wait_css('#card-pf-storage-pools > h2 > button',
                                 cond=clickable))
        self.wait_css('#storage-pools-listing')
        el_prefix = self.create_storage_by_ui(name=pool_name,
                                              storage_type='iscsi',
                                              target_path='/dev/disk/by-path',
                                              host='127.0.0.1',
                                              source_path=iqn)
        self.wait_css('#{}-name'.format(el_prefix))
        self.click(self.wait_css('#app div a', cond=clickable))
        self.wait_css('#virtual-machines-listing')

        disc.clear()
