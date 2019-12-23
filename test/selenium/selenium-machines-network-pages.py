from testlib_avocado.seleniumlib import clickable, text_in, invisible
from testlib_avocado.machineslib import MachinesLib
from selenium.webdriver.common.action_chains import ActionChains
from testlib_avocado.timeoutlib import wait


class MachinesNetworksTestSuite(MachinesLib):
    """
    :avocado: enable
    :avocado: tags=machines
    """

    def testNetworkInfo(self):
        net_cmd_active = int(self.machine.execute('sudo virsh net-list | awk \'NR>=3{if($0!="")print}\' | wc -l')) + int(
            self.machine.execute('virsh net-list | awk \'NR>=3{if($0!="")print}\' | wc -l'))
        print(net_cmd_active)
        print(self.wait_css('#card-pf-networks > div > p > span:nth-child(1)'))
        print(self.wait_css('#card-pf-networks > div > p > span:nth-child(1)').text)
        self.wait_css('#card-pf-networks > div > p > span:nth-child(1)',
                      cond=text_in,
                      text_=str(net_cmd_active))

        total = int(self.wait_css(
            '#card-pf-networks > div > p > span:nth-child(1)').text)
        active = int(self.wait_css(
            '#card-pf-networks > div > p > span:nth-child(1)').text)
        inactive = int(self.wait_css(
            '#card-pf-networks > div > p > span:nth-child(2)').text)

        self.assertEqual(total, active + inactive)
        # switch to the network page
        self.click(self.wait_css('#card-pf-networks > h2 > button',
                                 cond=clickable))
        self.wait_css('#networks-listing')

        page_active = 0
        page_inactive = 0

        el_group = self.driver.find_elements_by_css_selector(
            '#networks-listing table tbody')
        self.assertEqual(len(el_group), total)

        for el in el_group:
            if el.find_element_by_css_selector(
                    'tr > td > span').text == 'active':
                page_active += 1
            elif el.find_element_by_css_selector(
                    'tr > td > span').text == 'inactive':
                page_inactive += 1

        net_cmd_total = int(self.machine.execute('sudo virsh net-list --all | awk \'NR>3{if($0!="")print}\' | wc -l')) + int(
            self.machine.execute('sudo virsh net-list --all | awk \'NR>3{if($0!="")print}\' | wc -l'))

        self.assertEqual(net_cmd_total, page_active + page_inactive)
        self.click(self.wait_css('#app div a'))
        self.wait_css('#networks-listing', cond=invisible)
        self.wait_css('#virtual-machines-listing')

    def testCheckStateOfNetwork(self):
        net_name = 'test_net' + MachinesLib.random_string()
        self.net_delete_list[net_name] = True
        self.create_network(net_name,
                            active=True)

        self.click(self.wait_css('#card-pf-networks > h2 > button',
                                 cond=clickable))
        self.click(self.wait_css('#network-{}-system-name'.format(net_name),
                                 cond=clickable))

        self.click(self.wait_css('#deactivate-network-{}-system'.format(net_name)))
        cmd_res = self.machine.execute('sudo virsh net-info {} | grep Active'.format(net_name))

        self.assertEqual(cmd_res.strip().split(" ")[-1],
                         'no')
        self.wait_css('#network-{}-system-state'.format(net_name),
                      cond=text_in,
                      text_='inactive')

        self.click(self.wait_css('#activate-network-{}-system'.format(net_name)))
        cmd_res = self.machine.execute('sudo virsh net-info {} | grep Active'.format(net_name))

        self.assertEqual(cmd_res.strip().split(" ")[-1],
                         'yes')
        self.wait_css('#network-{}-system-state'.format(net_name),
                      cond=text_in,
                      text_='active')

    def testNetworkAutoStart(self):
        net_name = 'test_net' + MachinesLib.random_string()
        self.net_delete_list[net_name] = True
        self.create_network(net_name,
                            active=True)

        self.click(self.wait_css('#card-pf-networks > h2 > button',
                                 cond=clickable))
        self.click(self.wait_css('#network-{}-system-name'.format(net_name),
                                 cond=clickable))

        wait(lambda: not self.wait_css('#network-{}-system-autostart-checkbox'.format(net_name)).is_selected())
        self.check_box(self.wait_css('#network-{}-system-autostart-checkbox'.format(net_name), cond=clickable))
        wait(lambda: self.wait_css('#network-{}-system-autostart-checkbox'.format(net_name)).is_selected())
        cmd_res = self.machine.execute('sudo virsh net-info {} | grep Autostart'.format(net_name))
        self.assertEqual(cmd_res.strip().split(" ")[-1], 'yes')
        wait(lambda: self.wait_css('#network-{}-system-autostart-checkbox'.format(net_name)).is_selected())
        self.check_box(self.wait_css('#network-{}-system-autostart-checkbox'.format(net_name), cond=clickable), checked=False)
        wait(lambda: not self.wait_css('#network-{}-system-autostart-checkbox'.format(net_name)).is_selected())
        cmd_res = self.machine.execute('sudo virsh net-info {} | grep Autostart'.format(net_name))
        self.assertEqual(cmd_res.strip().split(" ")[-1], 'no')

    def testTransientNetworkDeletion(self):
        net_1 = 'test_net_deletion_' + MachinesLib.random_string()
        self.net_delete_list[net_1] = False

        self.click(self.wait_css('#card-pf-networks > h2 > button',
                                 cond=clickable))
        self.create_network(net_1, persistent=False)
        self.click(self.wait_css('#network-{}-system-name'.format(net_1),
                                 cond=clickable))
        self.assertTrue(self.wait_css('#delete-network-{}-system'.format(net_1)).get_attribute('disabled'))
        ActionChains(self.driver).move_to_element(self.wait_css('#delete-network-{}-system'.format(net_1))).perform()
        self.wait_css('#delete-network-{}-system-tooltip div.tooltip-inner'.format(net_1),
                      cond=text_in,
                      text_="Non-persistent network cannot be deleted. It ceases to exists when it's deactivated.")
