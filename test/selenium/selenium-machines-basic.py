import os
import re
from avocado import skipIf
from testlib_avocado.timeoutlib import wait
from testlib_avocado.timeoutlib import TimeoutError
from testlib_avocado.seleniumlib import clickable, invisible, text_in
from testlib_avocado.machineslib import MachinesLib
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


class MachinesBasicTestSuite(MachinesLib):
    """
    :avocado: enable
    :avocado: tags=machines
    """

    def testNoVm(self):
        self.wait_text("No VM is running or defined on this host")

    def testOverviewInfo(self):
        name = "staticvm"
        self.create_vm(name)

        self.check_vm_info(name)

    def testRunVm(self):
        name = "staticvm"
        args = self.create_vm(name, state='shut off')

        self.click(self.wait_css('#vm-{}-run'.format(name), cond=clickable))
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='running')
        self.wait_css('#vm-{}-run'.format(name), cond=invisible)
        self.wait_css('#vm-{}-reboot'.format(name))
        self.wait_css('#vm-{}-off'.format(name))
        self.wait_css('#vm-{}-delete'.format(name))
        self.wait_vm_complete_start(args)

    def testRestartVm(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-reboot'.format(name), cond=clickable))
        wait(lambda: "reboot: Power down" in self.machine.execute("sudo cat {0}".format(args.get('logfile'))), delay=3)
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='running')

    def testForceRestartVm(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        def force_reboot_operation():
            self.click(self.wait_css('#vm-{}-reboot-caret'.format(name), cond=clickable))
            self.click(self.wait_css('#vm-{}-forceReboot'.format(name), cond=clickable))
            wait(lambda: re.search("login:.*Initializing cgroup",
                                   self.machine.execute("sudo cat {0}".format(args.get('logfile')))), tries=10)

        # Retry when running in edge
        # because the first operations will not take effect in some edge browser
        # The error will be throw if timeout at the second time
        try:
            force_reboot_operation()
        except TimeoutError:
            force_reboot_operation()

        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='running')

    def testShutdownVm(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-off'.format(name), cond=clickable))
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='shut off')
        wait(lambda: "reboot: Power down" in self.machine.execute("sudo cat {0}".format(args.get('logfile'))), delay=3)
        self.wait_css('#vm-{}-run'.format(name))
        self.click(self.wait_css('#vm-{}-consoles'.format(name), cond=clickable))
        self.wait_text("Please start the virtual machine to access its console.", element="div")

    def testForceShutdownVm(self):
        name = "staticvm"
        self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-off-caret'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-forceOff'.format(name), cond=clickable))
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='shut off')
        self.wait_css('#vm-{}-run'.format(name))
        self.click(self.wait_css('#vm-{}-consoles'.format(name), cond=clickable))
        self.wait_text("Please start the virtual machine to access its console.", element="div")

    def testSendNMI(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-off-caret'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-sendNMI'.format(name), cond=clickable))
        wait(lambda: "NMI received" in self.machine.execute("sudo cat {0}".format(args.get('logfile'))), delay=3)
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='running')

    def testDelete(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        imgdel = "{}/imagetest.img".format(args.get('poolPath'))
        self.machine.execute(
            "sudo qemu-img create -f raw {} 128M && sudo virsh pool-refresh {}".format(imgdel, args.get('poolName')))
        self.machine.execute("sudo virsh attach-disk {} {} vda".format(name, imgdel))
        self.click(self.wait_css('#vm-{}-disks'.format(name), cond=clickable))
        self.wait_css('#vm-{}-disks-vda-bus'.format(name))

        self.click(self.wait_css("#vm-{}-delete".format(name), cond=clickable))
        self.click(self.wait_css("#vm-{}-delete-modal-dialog li:nth-of-type(1) input".format(name), cond=clickable))
        self.click(self.wait_css("#vm-{}-delete-modal-dialog button.btn-danger".format(name), cond=clickable))
        self.wait_css("#vm-{}-row".format(name), cond=invisible)

        self.machine.execute("while test -f {}; do sleep 1; done".format(imgdel))
        self.assertNotIn(name, self.machine.execute("sudo virsh list --all"))
        self.assertNotIn(imgdel, self.machine.execute("sudo virsh vol-list {}".format(args.get('poolName'))))
        self.assertIn(args.get('image'), self.machine.execute("sudo virsh vol-list {}".format(args.get('poolName'))))

    def testVmStatus(self):
        name = 'staticvm'
        self.create_vm(name)

        self.assertEqual(
            self.machine.execute('sudo virsh domstate {}'.format(name)).rstrip(),
            self.wait_css('#vm-{}-state'.format(name)).text)

    @skipIf(os.environ.get("BROWSER") == 'edge',
            "fails too often, https://github.com/cockpit-project/cockpit/issues/13072")
    def testCreateVMWithISO(self):
        name = 'test_iso'
        iso_path = '/home/{}.iso'.format(name + MachinesLib.random_string())
        self.vm_stop_list.append(name)

        self.machine.execute('sudo touch {}'.format(iso_path))

        self.create_vm_by_ui(connection='session',
                             name=name,
                             source=iso_path,
                             mem=128,
                             mem_unit='M',
                             storage=50,
                             storage_unit='M')

    @skipIf(os.environ.get('URLSOURCE') is None,
            "Need an environment variable named 'URLSOURCE'")
    def testCreateVMWithUrl(self):
        name = 'test_url'
        self.vm_stop_list.append(name)

        self.create_vm_by_ui(connection='session',
                             name=name,
                             source_type='url',
                             source=os.environ.get('URLSOURCE'),
                             immediately_start=True)

        self.wait_css('#vm-{}-row'.format(name))
        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='creating VM installation')
        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='running',
                      overridetry=300)
        self.wait_css('div.toolbar-pf-results canvas')

    def testCreateVMWithExisting(self):
        name = 'test_existing_' + MachinesLib.random_string()
        base_path = '/var/lib/libvirt/images/cirros.qcow2'
        dest_path = '/home/cirros.qcow2'
        cmd = 'sudo test -f {base} && sudo cp {base} {dest} && sudo chmod 777 {dest}'
        self.machine.execute(cmd.format(base=base_path, dest=dest_path))
        self.vm_stop_list.append(name)

        self.create_vm_by_ui(connection='session',
                             name=name,
                             source_type='disk_image',
                             source=dest_path)

    def testCheckOSRecommendMemory(self):
        self.click(self.wait_css('#create-new-vm', cond=clickable))
        self.select_by_value(self.wait_css('#source-type', cond=clickable),
                             'file')
        self.send_keys(self.wait_css('label[for=os-select] + div > div > div > input'),
                       'SUSE CaaS Platform 3.0')
        self.send_keys(self.wait_css('label[for=os-select] + div > div > div > input'),
                                     Keys.ARROW_DOWN + Keys.ENTER)
        ActionChains(self.driver).move_to_element(self.wait_css('#memory-size-slider > div.slider-handle.min-slider-handle.round')).perform()
        self.assertEqual(self.wait_css('#memory-size-slider .tooltip.tooltip-main.top .tooltip-inner').text.strip(),
                         '8')

        self.click(self.wait_css('button.btn-cancel.btn.btn-default',
                                 cond=clickable))

        self.click(self.wait_css('#create-new-vm', cond=clickable))
        self.select_by_value(self.wait_css('#source-type', cond=clickable),
                             'file')
        self.send_keys(self.wait_css('label[for=os-select] + div > div > div > input'),
                       'Pop!_OS 18.04')
        self.send_keys(self.wait_css('label[for=os-select] + div > div > div > input'),
                                     Keys.ARROW_DOWN + Keys.ENTER)
        # can not use the same ActionChains object as there will be an error raised which is 
        # 'stale element reference: element is not attached to the page document'.Although the 
        # code has already finished
        ActionChains(self.driver).move_to_element(self.wait_css('#memory-size-slider > div.slider-handle.min-slider-handle.round')).perform()
        self.assertEqual(self.wait_css('#memory-size-slider .tooltip.tooltip-main.top .tooltip-inner').text.strip(),
                         '4')

    def testCreateVMWithDifferentDisk(self):
        def createvm(storage_pool):
            name = 'test_' + MachinesLib.random_string()
            iso_path = '/home/{}.iso'.format(name)
            self.machine.execute('sudo touch {}'.format(iso_path))
            self.vm_stop_list.append(name)

            if storage_pool == 'NoStorage':
                self.create_vm_by_ui(connection='session',
                                     name=name,
                                     source=iso_path,
                                     storage_pool=storage_pool,
                                     mem=128,
                                     mem_unit='M')
            elif storage_pool == 'NewVolume':
                self.create_vm_by_ui(connection='session',
                                     name=name,
                                     source=iso_path,
                                     storage=50,
                                     storage_unit='M',
                                     mem=128,
                                     mem_unit='M')
            elif storage_pool == 'default':
                vol_name = 'vol_test_' + MachinesLib.random_string()
                self.machine.execute('virsh vol-create-as default {} 1M'.format(vol_name))
                self.refresh_machines_page()
                self.create_vm_by_ui(connection='session',
                                     name=name,
                                     source=iso_path,
                                     storage_pool=storage_pool,
                                     volume_name=vol_name,
                                     mem=128,
                                     mem_unit='M')

        createvm('NewVolume')
        createvm('NoStorage')
        createvm('default')

    def testCheckHostAvailableSpace(self):
        if 'default' not in self.machine.execute('virsh pool-list --all'):
            self.machine.execute('virsh pool-define-as default '
                                 + '--type dir '
                                 + '--target ~/.local/share/libvirt/images '
                                 + '&& virsh pool-start default')
        pool_default = int(float(self.machine.execute(
            'virsh pool-info --bytes default | grep Available').strip().split(" ")[-1]) / 1024 / 1024 / 1024)

        self.click(self.wait_css('#create-new-vm', cond=clickable))
        self.click(self.wait_css('#connection > div > label:nth-child(2) > input[type=radio]'))
        self.assertIn(str(pool_default),
                      self.wait_css('#storage-size-slider + input + b').text)

    def testSetAutostartForRunnigVM(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name)
        wait(lambda: not self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        # check autostart of the VM
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable))
        wait(lambda: self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'enable')
        # uncheck autostart of the VM
        wait(lambda: self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable),
                       checked=False)
        wait(lambda: not self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'disable')

    def testSetAutostartForOffVM(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name, state='shut off')
        # check autostart of the VM
        wait(lambda: not self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable))
        wait(lambda: self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'enable')
        # uncheck autostart of the VM
        wait(lambda: self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable),
                       checked=False)
        wait(lambda: not self.wait_css('#vm-{}-autostart-checkbox'.format(name)).is_selected())
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'disable')

    def testCheckBootOrderInfo(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name)

        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.wait_css('#vm-{}-order-modal-device-row-0'.format(name))
        self.wait_css('#vm-{}-order-modal-device-row-1'.format(name))

        self.assertEqual(self.wait_css('#vm-{}-order-modal-device-row-0 div.ct-form span'.format(name)).text,
                         '/var/lib/libvirt/images/cirros.qcow2')

        cmd_result = self.machine.execute(
            'sudo virsh dumpxml {} | grep \'mac address\''.format(name))
        self.assertEqual(self.wait_css('#vm-{}-order-modal-device-row-1 div.ct-form span'.format(name)).text,
                         cmd_result.strip().split('=')[-1].split('/')[0].strip('\''))

        self.click(self.wait_css('#vm-{}-order-modal-window button.close'.format(name),
                                 cond=clickable))

        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-cancel'.format(name),
                                 cond=clickable))

    def testAddDiskBootOption(self):
        name = 'test_' + MachinesLib.random_string()
        vol_path = '/var/lib/libvirt/images/test_' + MachinesLib.random_string()
        self.create_vm(name, state='shut off')
        self.machine.execute('sudo qemu-img create -f qcow2 {} 1M'.format(vol_path))
        self.machine.execute('sudo virsh attach-disk {} {} vdb --persistent'.format(name, vol_path))
        # refresh to make sure the new added disk can be appear on the apge
        self.driver.refresh()
        self.wait_frame('machines')
        self.click(self.wait_css('#vm-{}-row'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-run'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-boot-order'.format(name), cond=clickable))
        # Check the information about the new boot option
        self.assertEqual(self.wait_css('#vm-{}-order-modal-device-row-2 div.ct-form span'.format(name)).text,
                         vol_path)
        # Change new disk to the first boot option
        self.click(self.wait_css('#vm-{}-order-modal-device-row-2-checkbox'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-device-row-2 #vm-{}-order-modal-up'.format(name, name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-device-row-1 #vm-{}-order-modal-up'.format(name, name),
                                 cond=clickable))
        self.assertEqual(self.wait_css('#vm-{}-order-modal-device-row-0 div.ct-form span'.format(name)).text,
                         vol_path)
        self.wait_css('#vm-{}-order-modal-min-message'.format(name),
                      cond=text_in,
                      text_="Changes will take effect after shutting down the VM")
        self.click(self.wait_css('#vm-{}-order-modal-save'.format(name),
                                 cond=clickable))
        # Check notification
        ActionChains(self.driver).move_to_element(self.wait_css('#boot-order-tooltip')).perform()
        self.wait_css('#tip-boot-order',
                      cond=text_in,
                      text_="Changes will take effect after shutting down the VM")

    def testBootFromNetwork(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name, state='shut off')

        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-device-row-1 button.btn.btn-default'.format(name),
                                 cond=clickable))
        self.assertEqual(self.wait_css('#vm-{}-order-modal-device-row-0  div.list-group-item-heading'.format(name)).text,
                         'network')
        self.click(self.wait_css('#vm-{}-order-modal-save'.format(name), cond=clickable))
        self.wait_css('#vm-{}-boot-order'.format(name),
                      cond=text_in,
                      text_='network,disk')

    def testInvertUniqueBootOption(self):
        name = 'test' + MachinesLib.random_string()
        source_path = '/tmp/test{}.iso'.format(MachinesLib.random_string())
        self.machine.execute('touch {}'.format(source_path))
        self.vm_stop_list.append(name)

        self.create_vm_by_ui(connection='session',
                             name=name,
                             source_type='disk_image',
                             source=source_path,
                             mem=128,
                             mem_unit='M',
                             immediately_start=True)
        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='running')
        self.click(self.wait_css('#vm-{}-overview'.format(name), cond=clickable))

        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.assertFalse(
            self.wait_css('#vm-{}-order-modal-device-row-0  button:nth-child(1)'.format(name)).is_enabled())
        self.assertFalse(
            self.wait_css('#vm-{}-order-modal-device-row-0  button:nth-child(2)'.format(name)).is_enabled())

        self.click(self.wait_css('#vm-{}-order-modal-device-row-0-checkbox'.format(name),
                                 cond=clickable))
        self.assertFalse(self.wait_css('#vm-{}-order-modal-device-row-0-checkbox'.format(name)).is_selected())
        self.wait_css('#vm-{}-order-modal-min-message'.format(name),
                      cond=text_in,
                      text_="Changes will take effect after shutting down the VM")
        self.click(self.wait_css('#vm-{}-order-modal-save'.format(name),
                                 cond=clickable))
        self.wait_css('#vm-{}-order-modal-window'.format(name),
                      cond=invisible)
        self.wait_css('#vm-{}-boot-order'.format(name),
                      cond=text_in,
                      text_='disk')
        self.wait_css('#boot-order-tooltip', cond=invisible)

        self.click(self.wait_css('#vm-{}-off-caret'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-forceOff'.format(name),
                                 cond=clickable))
        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='shut off')

        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-device-row-0-checkbox'.format(name),
                                 cond=clickable))
        self.assertFalse(self.wait_css('#vm-{}-order-modal-device-row-0-checkbox'.format(name)).is_selected())
        self.wait_css('#vm-{}-order-modal-min-message'.format(name),
                      cond=invisible)
        self.click(self.wait_css('#vm-{}-order-modal-save'.format(name),
                                 cond=clickable))
        self.wait_css('#vm-{}-order-modal-window'.format(name),
                      cond=invisible)
        self.wait_css('#vm-{}-boot-order'.format(name),
                      cond=text_in,
                      text_='disk')
        self.wait_css('#boot-order-tooltip', cond=invisible)

    def testEditVMBootOrder(self):
        name = 'test_' + MachinesLib.random_string()
        source_path = '/tmp/test_' + MachinesLib.random_string()
        self.machine.execute('touch {}'.format(source_path))
        self.vm_stop_list.append(name)
        # Add network for the second boot option when VM running
        self.create_vm_by_ui(connection='session',
                             name=name,
                             source_type='disk_image',
                             source=source_path,
                             mem=128,
                             mem_unit='M',
                             immediately_start=True)
        self.click(self.wait_css('#vm-{}-overview'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-boot-order'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-device-row-1-checkbox'.format(name),
                                 cond=clickable))
        self.assertTrue(self.wait_css('#vm-{}-order-modal-device-row-1-checkbox'.format(name),
                                      cond=clickable).is_selected())
        self.wait_css('#vm-{}-order-modal-min-message'.format(name),
                      cond=text_in,
                      text_="Changes will take effect after shutting down the VM")
        self.click(self.wait_css('#vm-{}-order-modal-save'.format(name), cond=clickable))
        self.wait_css('#vm-{}-order-modal-window'.format(name), cond=invisible)
        self.wait_css('#boot-order-tooltip')
        ActionChains(self.driver).move_to_element(self.wait_css('#boot-order-tooltip')).perform()
        self.wait_css('#tip-boot-order',
                      cond=text_in,
                      text_="Changes will take effect after shutting down the VM")
        # Force off the VM
        self.click(self.wait_css('#vm-{}-off-caret'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-forceOff'.format(name),
                                 cond=clickable))
        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='shut off')
        self.assertEqual(self.wait_css('#vm-{}-boot-order'.format(name)).text,
                         'disk,network')
        # Change network to the first boot option when VM off
        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{name}-order-modal-device-row-1 #vm-{name}-order-modal-up'.format(name=name),
                                 cond=clickable))
        self.wait_css('#vm-{}-order-modal-min-message'.format(name),
                      cond=invisible)
        self.wait_css('#vm-{}-order-modal-device-row-0 div.list-group-item-heading'.format(name),
                      cond=text_in,
                      text_='network')
        self.click(self.wait_css('#vm-{}-order-modal-save'.format(name), cond=clickable))
        self.wait_css('#vm-{}-order-modal-window'.format(name), cond=invisible)
        self.assertEqual(self.wait_css('#vm-{}-boot-order'.format(name)).text,
                         'network,disk')
        self.wait_css('#boot-order-tooltip', cond=invisible)
        # Change disk to the first boot option when VM off
        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{name}-order-modal-device-row-0 #vm-{name}-order-modal-down'.format(name=name),
                                 cond=clickable))
        self.wait_css('#vm-{}-order-modal-min-message'.format(name), cond=invisible)
        self.wait_css('#vm-{}-order-modal-device-row-0 div.list-group-item-heading'.format(name),
                      cond=text_in,
                      text_='disk')
        self.click(self.wait_css('#vm-{}-order-modal-save'.format(name), cond=clickable))
        self.wait_css('#vm-{}-order-modal-window'.format(name), cond=invisible)
        self.assertEqual(self.wait_css('#vm-{}-boot-order'.format(name)).text,
                         'disk,network')
        self.wait_css('#boot-order-tooltip', cond=invisible)
