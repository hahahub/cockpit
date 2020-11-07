import os
import re
from avocado import skipIf
from testlib_avocado.timeoutlib import wait
from testlib_avocado.seleniumlib import clickable, invisible, text_in
from testlib_avocado.machineslib import MachinesLib
from selenium.webdriver.common.action_chains import ActionChains


class MachinesBasicTestSuite(MachinesLib):
    """
    :avocado: enable
    :avocado: tags=machines
    """

    def testNoVm(self):
        self.wait_css('thead.ct-table-empty tr td',
                      cond=text_in,
                      text_='No VM is running or defined on this host')

    def testOverviewInfo(self):
        name = "staticvm"
        self.create_vm(name)
        self.goToVMPage(name)

        self.check_vm_info(name)

    def testRunVm(self):
        name = "staticvm"
        args = self.create_vm(name, state='Shut off')

        self.click(self.wait_css('#vm-{}-run'.format(name), cond=clickable))
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='Running')
        self.wait_css('#vm-{}-run'.format(name), cond=invisible)
        self.wait_css('#vm-{}-shutdown-button'.format(name))
        self.wait_vm_complete_start(args)

    def testRestartVm(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-action-kebab button'.format(name), cond=clickable))
        self.wait_css('ul.pf-c-dropdown__menu.pf-m-align-right')
        self.click(self.wait_css('#vm-{}-reboot'.format(name), cond=clickable))
        wait(lambda: "reboot: Power down" in self.machine.execute("sudo cat {0}".format(args.get('logfile'))), delay=3)
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='Running')

    def testForceRestartVm(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-action-kebab button'.format(name), cond=clickable))
        self.wait_css('ul.pf-c-dropdown__menu.pf-m-align-right')
        self.click(self.wait_css('#vm-{}-forceReboot'.format(name), cond=clickable))
        wait(lambda: re.search("login:.*Initializing cgroup",
                               self.machine.execute("sudo cat {0}".format(args.get('logfile')))))

        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='Running')

    def testShutdownVm(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-shutdown-button'.format(name), cond=clickable))
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='Shut off')
        wait(lambda: "reboot: Power down" in self.machine.execute("sudo cat {0}".format(args.get('logfile'))), delay=3)
        self.wait_css('#vm-{}-run'.format(name))
        self.goToVMPage(name)
        self.click(self.wait_css('#vm-{}-consoles'.format(name), cond=clickable))
        self.wait_text("Please start the virtual machine to access its console.", element="div")

    def testForceShutdownVm(self):
        name = "staticvm"
        self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-action-kebab button'.format(name), cond=clickable))
        self.wait_css('ul.pf-c-dropdown__menu.pf-m-align-right')
        self.click(self.wait_css('#vm-{}-forceOff'.format(name), cond=clickable))
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='Shut off')
        self.wait_css('#vm-{}-run'.format(name))
        self.goToVMPage(name)
        self.click(self.wait_css('#vm-{}-consoles'.format(name), cond=clickable))
        self.wait_text("Please start the virtual machine to access its console.", element="div")

    def testSendNMI(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)

        self.click(self.wait_css('#vm-{}-action-kebab button'.format(name), cond=clickable))
        self.wait_css('ul.pf-c-dropdown__menu.pf-m-align-right')
        self.click(self.wait_css('#vm-{}-sendNMI'.format(name), cond=clickable))
        wait(lambda: "NMI received" in self.machine.execute("sudo cat {0}".format(args.get('logfile'))), delay=3)
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='Running')

    def testDelete(self):
        name = "staticvm"
        args = self.create_vm(name, wait=True)
        imgdel = "{}/imagetest.img".format(args.get('poolPath'))

        self.machine.execute(
            "sudo qemu-img create -f raw {} 128M && sudo virsh pool-refresh {}".format(imgdel, args.get('poolName')))
        self.machine.execute("sudo virsh attach-disk {} {} vda".format(name, imgdel))
        self.goToVMPage(name)
        self.wait_css('#vm-{}-disks-vda-bus'.format(name))

        self.click(self.wait_css('#vm-{}-action-kebab button'.format(name), cond=clickable))
        self.wait_css('ul.pf-c-dropdown__menu.pf-m-align-right')
        self.click(self.wait_css("#vm-{}-delete".format(name), cond=clickable))
        self.click(self.wait_css("#vm-{}-delete-modal-dialog li:nth-of-type(1) input".format(name), cond=clickable))
        self.click(self.wait_css("#vm-{}-delete-modal-dialog button.pf-c-button.pf-m-danger".format(name), cond=clickable))
        self.wait_css("#vm-{}-state".format(name), cond=invisible)

        wait(lambda: self.machine.execute("! test -f %s && echo $?" % imgdel))
        wait(lambda: name not in self.machine.execute("sudo virsh list --all"))
        wait(lambda: imgdel not in self.machine.execute("sudo virsh vol-list {}".format(args.get('poolName'))))
        wait(lambda: args.get('image') in self.machine.execute("sudo virsh vol-list {}".format(args.get('poolName'))))

    def testVmStatus(self):
        name = 'staticvm'
        self.create_vm(name)

        self.assertEqual(
            self.machine.execute('sudo virsh domstate {}'.format(name)).rstrip(),
            self.wait_css('#vm-{}-state'.format(name)).text.lower())

    @skipIf(os.environ.get("BROWSER") == 'edge',
            "fails too often, https://github.com/cockpit-project/cockpit/issues/13072")
    def testCreateVMWithISO(self):
        name = 'test_iso'
        iso_path = '/var/tmp/{}.iso'.format(name + MachinesLib.random_string())
        self.machine.execute('sudo touch {}'.format(iso_path))
        self.vm_stop_list.append(name)

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
                             operating_system=None,
                             immediately_start=True)

        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='Running',
                      overridetry=300)
        self.goToVMPage(name, "session")
        self.wait_css('div.toolbar-pf-results canvas')

    def testCreateVMWithExisting(self):
        name = 'test_existing_' + MachinesLib.random_string()
        base_path = '/var/lib/libvirt/images/cirros.qcow2'
        dest_path = '/var/tmp/cirros.qcow2'
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

        for s in "SUSE CaaS Platform 3.0":
            self.send_keys(self.wait_css('label[for=os-select] + div input',
                                         cond=clickable),
                           s,
                           clear=False)
        self.click(self.wait_css("#os-select button", cond=clickable))

        mem_host = self.machine.execute("free -gt | awk 'NR==2{print $2}'").strip()
        ActionChains(self.driver).move_to_element(self.wait_css('#memory-size-slider > div.slider-handle.min-slider-handle.round')).perform()
        self.assertEqual(self.wait_css('#memory-size-slider .tooltip.tooltip-main.top .tooltip-inner').text.strip(),
                         mem_host if int(mem_host) < 8 else '8')

        # clear the input
        self.send_keys(self.wait_css('label[for=os-select] + div input',
                                     cond=clickable), "")
        for s in "Pop!_OS 18.04":
            self.send_keys(self.wait_css('label[for=os-select] + div input',
                                         cond=clickable),
                           s,
                           clear=False)
        self.click(self.wait_css("#os-select button", cond=clickable))
        ActionChains(self.driver).move_to_element(self.wait_css('#memory-size-slider > div.slider-handle.min-slider-handle.round')).perform()
        self.assertEqual(self.wait_css('#memory-size-slider .tooltip.tooltip-main.top .tooltip-inner').text.strip(),
                         mem_host if int(mem_host) < 4 else '4')

    def testCreateVMWithDifferentDisk(self):
        def createRandomVmNameAndFile():
            name = 'test_' + MachinesLib.random_string()
            iso_path = '/var/tmp/{}.iso'.format(name)
            self.machine.execute('sudo touch {}'.format(iso_path))
            self.vm_stop_list.append(name)

            return [name, iso_path]

        tmp = createRandomVmNameAndFile()
        self.create_vm_by_ui(connection='session',
                             name=tmp[0],
                             source=tmp[1],
                             storage_pool='NoStorage',
                             mem=128,
                             mem_unit='M')

        tmp = createRandomVmNameAndFile()
        self.create_vm_by_ui(connection='session',
                             name=tmp[0],
                             source=tmp[1],
                             storage=50,
                             storage_unit='M',
                             mem=128,
                             mem_unit='M')

        tmp = createRandomVmNameAndFile()
        vol_name = 'vol_test_' + MachinesLib.random_string()
        self.machine.execute('virsh vol-create-as default {} 1M'.format(vol_name))
        self.refresh_machines_page()
        self.create_vm_by_ui(connection='session',
                             name=tmp[0],
                             source=tmp[1],
                             storage_pool='default',
                             volume_name=vol_name,
                             mem=128,
                             mem_unit='M')

    def testCheckHostAvailableSpace(self):
        if 'default' not in self.machine.execute('virsh pool-list --all'):
            self.machine.execute('virsh pool-define-as default ' +
                                 '--type dir ' +
                                 '--target ~/.local/share/libvirt/images ' +
                                 '&& virsh pool-start default')
        pool_default = int(float(self.machine.execute('virsh pool-info --bytes default | grep Available').strip().split(" ")[-1]) / 1024 / 1024 / 1024)

        self.click(self.wait_css('#create-new-vm', cond=clickable))
        self.click(self.wait_css('#connection > div > label:nth-child(2) > input[type=radio]'))
        self.assertIn(str(pool_default),
                      self.wait_css('#storage-size-slider + input + b').text)

    def testSetAutostartForRunnigVM(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name)
        self.goToVMPage(name)
        # check autostart of the VM
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable))
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'enable')
        # uncheck autostart of the VM
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable),
                       checked=False)
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'disable')

    def testSetAutostartForOffVM(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name, state='Shut off')
        self.goToVMPage(name)
        # check autostart of the VM
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable))
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'enable')
        # uncheck autostart of the VM
        self.check_box(self.wait_css('#vm-{}-autostart-checkbox'.format(name),
                                     cond=clickable),
                       checked=False)
        cmd_res = self.machine.execute('sudo virsh dominfo {} | grep Autostart'.format(name)).strip().split(" ")[-1]
        self.assertEqual(cmd_res, 'disable')

    def testCheckBootOrderInfo(self):
        name = 'test_' + MachinesLib.random_string()
        self.create_vm(name)
        self.goToVMPage(name)

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

        self.click(self.wait_css('#vm-{}-order-modal-window button.pf-c-button.pf-m-plain'.format(name),
                                 cond=clickable))
        self.wait_css("#vm-{}-order-modal-window".format(name), cond=invisible)

        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-cancel'.format(name),
                                 cond=clickable))
        self.wait_css("#vm-{}-order-modal-window".format(name), cond=invisible)

    def testAddDiskBootOption(self):
        name = 'test_' + MachinesLib.random_string()
        vol_path = '/var/lib/libvirt/images/test_' + MachinesLib.random_string()
        self.create_vm(name, state='Shut off')
        self.machine.execute('sudo qemu-img create -f qcow2 {} 1M'.format(vol_path))
        self.machine.execute('sudo virsh attach-disk {} {} vdb --persistent'.format(name, vol_path))
        # refresh to make sure the new added disk can be appear on the apge
        self.driver.refresh()
        self.wait_frame('machines')
        self.goToVMPage(name)
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
        self.create_vm(name, state='Shut off')
        self.goToVMPage(name)

        self.click(self.wait_css('#vm-{}-boot-order'.format(name),
                                 cond=clickable))
        self.click(self.wait_css('#vm-{}-order-modal-device-row-1 button.pf-c-button.pf-m-primary'.format(name),
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
                      text_='Running')
        self.goToVMPage(name, "session")

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

        self.click(self.wait_css('#vm-{}-action-kebab button'.format(name), cond=clickable))
        self.click(self.wait_css('#vm-{}-forceOff'.format(name),
                                 cond=clickable))
        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='Shut off')

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
        self.goToVMPage(name, "session")
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
        self.click(self.wait_css('#vm-{}-action-kebab button'.format(name), cond=clickable))
        self.wait_css('ul.pf-c-dropdown__menu.pf-m-align-right')
        self.click(self.wait_css('#vm-{}-forceOff'.format(name),
                                 cond=clickable))
        self.wait_css('#vm-{}-state'.format(name),
                      cond=text_in,
                      text_='Shut off')
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
