Vagrant.configure("2") do |config|

  # VM1 - Machine Normale
  config.vm.define "vm1" do |vm1|
    vm1.vm.box = "ubuntu/jammy64"
    vm1.vm.hostname = "vm1-normal"
    vm1.vm.network "private_network", ip: "192.168.56.10"
    vm1.vm.provider "virtualbox" do |vb|
      vb.name = "VM1-Normal"
      vb.memory = "2048"
      vb.cpus = 2
    end
  end

  # VM2 - Serveur Cible
  config.vm.define "vm2" do |vm2|
    vm2.vm.box = "ubuntu/jammy64"
    vm2.vm.hostname = "vm2-serveur"
    vm2.vm.network "private_network", ip: "192.168.56.20"
    vm2.vm.provider "virtualbox" do |vb|
      vb.name = "VM2-Serveur"
      vb.memory = "2048"
      vb.cpus = 2
    end
  end

end