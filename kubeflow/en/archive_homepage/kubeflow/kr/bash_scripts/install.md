



```bash
#!/bin/bash
#  install_kubernetes
#    Tested on Ubuntu 18.04 LTS
#
#  * Rev.2: 2020-07-16 (Thu)
#  * Rev.1: 2020-07-15 (Wed)
#  * Draft: 2020-07-14 (Tue)
#
#  Usage:
#    To run this script, 
#      $ chmod +x install_kubernetes
#      $ ./install_kubernetes
#
#    To edit this file, use a text editor.
#      $ nano install_kubernetes
#    nano is my choice of text editor, but you may use other text editor such as vi, vim, or emacs.

# Overview: there are two parts in this script.
#   1. Function Definitions
#   2. Main

#========================#
#  Function Definitions  #
#========================#
# Used both for master and worker nodes
deactivate_swap_memory() {
  printf "\nDeactivating Swap Memory...\n"
  sudo swapoff -a  # Turn off all swap memory

  # Comment out the line starting with /swapfile
  awk '{ if ($0 ~ /^\/swapfile/ ) { printf("#%s\n",$0); } else { print $0; }}' /etc/fstab > fstab
  sudo cp /etc/fstab /etc/fstab.backup
  sudo mv fstab /etc/fstab

  # On Ubuntu, the last line is commented out to deactivate swap memory.
  tail -n 1 /etc/fstab
}

get_installed_packages() {
  # To verify if Docker exists or is uninstalled.
  INSTALLED_PACKAGES=`dpkg -l | grep -i docker`
  echo "INSTALLED_PACKAGES for Docker"
  echo "$INSTALLED_PACKAGES"
}

uninstall_docker() {
  printf "\nUninstalling Docker...\n"

  # Remove the installed packages
  sudo apt-get purge -y docker-engine docker docker.io docker-ce docker-ce-cli
  sudo apt-get autoremove -y --purge docker-engine docker docker.io docker-ce

  # Remove the remnants
  sudo rm -rf /var/lib/docker /etc/docker
  sudo rm /etc/apparmor.d/docker
  sudo groupdel docker
  sudo rm -rf /var/run/docker.sock
}

install_docker() {
  printf "\nInstalling Docker...\n"

  # https://docs.docker.com/engine/install/ubuntu/
  # https://kubernetes.io/docs/setup/production-environment/container-runtimes/

  CONTAINERD_VERSION="1.2.13-2"
  VERSION_STRING="5:19.03.11~3-0~ubuntu-$(lsb_release -cs)"
  #echo $VERSION_STRING  # 5:19.03.11~3-0~ubuntu-bionic

  sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common gnupg2
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg |  apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  #apt-get update &&  apt-get install -y containerd.io docker-ce docker-ce-cli
  sudo apt-get update
  sudo apt-get install -y docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io=$CONTAINERD_VERSION

  # Error occured even with the sudo command.
  # bash: /etc/docker/daemon.json: No such file or directory
  # There is no directory /etc/docker.
  # So the command is broken into several parts.
  sudo mkdir /etc/docker
  cat > daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF
  sudo mv daemon.json /etc/docker/daemon.json
  # Question if the above part is necessary as Docker's installation manual doesn't have this part.
  # https://github.com/kubernetes/kubeadm/issues/1394

  sudo mkdir -p /etc/systemd/system/docker.service.d
  sudo systemctl daemon-reload
  sudo systemctl restart docker
}

configure_docker() {
  printf "\nConfiguring Docker as the post-installation steps...\n"

  # Configure Linux / Manage Docker as a non-root user
  sudo groupadd docker
  sudo usermod -aG docker $USER

  # Step 3. Log out and log back in so that your group membership is re-evaluated.
  # Just closing the terminal and re-opening it doesn't work. If testing on a virtual machine, 
  #   it may be necessary to restart the virtual machine for changes to take effect.

  # Configure Docker to Start on Boot
  sudo systemctl enable docker
}

verify_docker() {
  sudo docker run hello-world
}

ask_to_reinstall() {
  while true; do
    read -p "Reinstall Docker? (y/n)" REPLY
    case $REPLY in
      [Yy]* ) break ;;
      [Nn]* ) echo "Exiting..."; exit 1; ;;
      * ) echo "Enter either yes or no." ;;
    esac
  done
}

safe_install_docker() {
  # Docker may or may not be installed in the machine.
  # safe_install_docker double-checks to install the most recent version compatible with Kubernetes
  MOST_RECENT_COMPATIBLE_DOCKER_VERSION="19.03.11"

  DOCKER_LOCATION=`which docker`
  if [ -z "$DOCKER_LOCATION" ]; then
    echo "Docker does not exist in this machine."
    DOCKER_VERSION=""
  else
    DOCKER_VERSION=`sudo docker version --format '{{.Server.Version}}'`  #19.03.12
    #DOCKER_VERSION="19.03.12"           # For debugging
  fi

  if [ -z $DOCKER_VERSION ]; then
    install_docker
    configure_docker
    verify_docker
  elif [ $DOCKER_VERSION == $RECOMMENDED_DOCKER_VERSION ];then
    echo "The current Docker version ${DOCKER_VERSION} matches the recommended version ${RECOMMENDED_DOCKER_VERSION}."
  else  # Equivalently, elif [ $DOCKER_VERSION != $RECOMMENDED_DOCKER_VERSION ];then
    echo "The current Docker version ${DOCKER_VERSION} does not match the recommended version ${RECOMMENDED_DOCKER_VERSION}."
    ask_to_reinstall

    uninstall_docker
    install_docker
    configure_docker
    verify_docker
  fi
}

install_kubeadm_kubelet_kubectl() {
  printf "\nInstalling kubeadm, kubelet, kubectl...\n"

  sudo apt-get update && sudo apt-get install -y apt-transport-https curl
  curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
  cat <<EOF | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb https://apt.kubernetes.io/ kubernetes-xenial main
EOF
  sudo apt-get update
  sudo apt-get install -y kubelet kubeadm kubectl
  sudo apt-mark hold kubelet kubeadm kubectl
}

install_common_parts() {  # used both for master and worker ndoes
  deactivate_swap_memory
  safe_install_docker
  install_kubeadm_kubelet_kubectl
}

# Used only for the master 
setup_master() {
  printf "\nSetting up a master or control-plane node...\n"

  #sudo kubeadm init
  sudo kubeadm init > sudo_kubeadm_init.log

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

  sudo kubectl apply -f https://docs.projectcalico.org/v3.14/manifests/calico.yaml
  kubectl get nodes
}

extract_command2join_worker_nodes() {
  TEMP_INPUT_FILE="sudo_kubeadm_init.log"
  TEMP_OUTPUT_FILE="command2join_worker_nodes.txt"

  printf "\nExtracting two lines of command to join a worker node from $TEMP_INPUT_FILE...\n"
  cat $TEMP_INPUT_FILE | grep "^kubeadm join.*--token" > $TEMP_OUTPUT_FILE
  cat $TEMP_INPUT_FILE | grep "^    --discovery-token-ca-cert-hash" >> $TEMP_OUTPUT_FILE

  cat $TEMP_OUTPUT_FILE
  #kubeadm join <control-plane-host>:<control-plane-port> --token <token> \
  #    --discovery-token-ca-cert-hash sha256:<hash>
  printf "The command is saved to $TEMP_OUTPUT_FILE.\n"
}

get_master_or_worker() {
  while true; do
    read -p "Is this master or worker node? (m/w) " REPLY
    case $REPLY in
      [Mm]* ) echo "master"; break; ;;
      [Ww]* ) echo "worker"; break; ;;
      * ) echo "Enter either m or w / master or worker." ;;
    esac
  done
}

append_command2this_file() {
  THIS_FILE="install_kubernetes"
  COMMAND2JOIN=`cat $TEMP_OUTPUT_FILE`  # Note TEMP_OUTPUT_FILE is a global variable.
  #kubeadm join <control-plane-host>:<control-plane-port> --token <token> \
  #    --discovery-token-ca-cert-hash sha256:<hash>

  printf "
if [ \$NODE_TYPE == 'worker' ]; then
  echo 'Install Kubernetes on a workder node.'
  install_common_parts
  $COMMAND2JOIN
fi" >> $THIS_FILE
}

# Used only for worker nodes
join_this_node() {
  printf "\njoin\n"
#  kubeadm join <control-plane-host>:<control-plane-port> --token <token> --discovery-token-ca-cert-hash sha256:<hash>
}

#==End of Function Definitions==#

#========#
#  Main  #
#========#
printf "Kubernetes will be installed on this machine.\n"
NODE_TYPE=`get_master_or_worker`
#echo $NODE_TYPE

if [ $NODE_TYPE == "master" ]; then
  printf "\nInstall Kubernetes on a master (control-plane) node.\n"
  install_common_parts
  setup_master
  extract_command2join_worker_nodes
  append_command2this_file
fi

# append_command2this_file will append commands for a worker below.
if [ $NODE_TYPE == 'worker' ]; then
  echo 'Install Kubernetes on a workder node.'
  install_common_parts
  kubeadm join <control-plane-host>:<control-plane-port> --token <token> \
      --discovery-token-ca-cert-hash sha256:<hash>
fi
```



  kubeadm join <control-plane-host>:<control-plane-port> --token <token> \
      --discovery-token-ca-cert-hash sha256:<hash>

  kubeadm join 192.168.0.109:6443 --token kpuql9.hcp4b6nsgatg1m32 \
    --discovery-token-ca-cert-hash sha256:44ee742e024ac9f0617a1b73f7129960908b79e6b5a5fcba208b0b25e1244edb 