Vagrant.configure("2") do |config|
  
  
  # Disable vbguest auto update
  if Vagrant.has_plugin?("vagrant-vbguest")
    config.vbguest.auto_update = false
  end

  

  # VM1 - Hybrid (Normal Traffic + Attacks)
  config.vm.define "vm1" do |vm1|
    vm1.vm.box = "ubuntu/jammy64"
    vm1.vm.hostname = "vm1-attacker"
    vm1.vm.network "private_network", ip: "192.168.56.10"
    vm1.vm.synced_folder "scripts/", "/home/vagrant/scripts"
    vm1.vm.provider "virtualbox" do |vb|
      vb.name = "VM1-Attacker"
      vb.memory = "2048"
      vb.cpus = 2
    end
    vm1.vm.provision "shell", inline: <<-SHELL
      apt-get update -y
      apt-get install -y nmap hydra hping3 curl wget apache2-utils
      chmod +x /home/vagrant/scripts/*.sh
      echo "VM1 ready !!"
    SHELL
  end

  # VM2 - Target + CICFlowMeter
  config.vm.define "vm2" do |vm2|
    vm2.vm.box = "ubuntu/jammy64"
    vm2.vm.hostname = "vm2-target"
    vm2.vm.network "private_network", ip: "192.168.56.20"
    vm2.vm.synced_folder "scripts/", "/home/vagrant/scripts"
    vm2.vm.provider "virtualbox" do |vb|
      vb.name = "VM2-Target"
      vb.memory = "3048"
      vb.cpus = 2
    end
    vm2.vm.provision "shell", inline: <<-SHELL
      apt-get update -y
      apt-get install -y apache2 openssh-server net-tools python3 python3-pip tshark
      pip3 install cicflowmeter
      systemctl enable apache2
      systemctl start apache2
      systemctl enable ssh
      systemctl start ssh
      chmod +x /home/vagrant/scripts/*.sh
      echo "VM2 ready !!"
    SHELL
  end

end