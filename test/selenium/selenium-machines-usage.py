from testlib_avocado.seleniumlib import clickable, text_in
from testlib_avocado.machineslib import MachinesLib


class MachinesUsageTestSuite(MachinesLib):
    """
    :avocado: enable
    :avocado: tags=machines
    """

    def testUsage(self):
        name = "staticvm"
        self.create_vm(name, state='Shut off')
        self.goToVMPage(name)

        self.wait_css("div.memory-usage-chart span.pf-c-progress__measure", cond=text_in, text_="0.0 / 64.0 MiB")
        self.wait_css("div.vcpu-usage-chart span.pf-c-progress__measure", cond=text_in, text_="0.0% of 1 vCPU")
        self.click(self.wait_css('#vm-{}-run'.format(name), cond=clickable))
        self.wait_css('#vm-{}-state'.format(name), cond=text_in, text_='Running')
        self.wait_css("div.memory-usage-chart span.pf-c-progress__measure",
                      cond=text_in,
                      reversed_cond=True,
                      text_="0.0 / 64.0 MiB")
