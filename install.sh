#!/bin/bash
# Secure P2P Communication Tool Installer
# This script installs required dependencies and sets up the tool on Kali Linux or Termux.

# Detect platform (Kali vs Termux)
platform=""
if [[ -d "/data/data/com.termux" ]]; then
    platform="termux"
elif [[ -f "/etc/os-release" ]] && grep -qi "Kali" /etc/os-release; then
    platform="kali"
else
    platform="linux"
fi

echo "Detected platform: $platform"

# Define package manager and packages for each platform
if [[ "$platform" == "termux" ]]; then
    PKG_INSTALL="pkg install -y"
    DEP_PACKAGES="python gnupg openssh"
    VPN_PACKAGE="openvpn"    # Termux has openvpn package, might require root for tun
    VOIP_PACKAGE=""          # No Mumble CLI in Termux
elif [[ "$platform" == "kali" ]]; then
    PKG_INSTALL="sudo apt-get install -y"
    DEP_PACKAGES="python3 gnupg openssh-client openssh-server"
    VPN_PACKAGE="openvpn"
    VOIP_PACKAGE="mumble"
else
    # Fallback for other Debian-based Linux
    PKG_INSTALL="sudo apt-get install -y"
    DEP_PACKAGES="python3 gnupg openssh-client"
    VPN_PACKAGE="openvpn"
    VOIP_PACKAGE="mumble"
fi

# Ask user which components to install
read -p "Install core messaging and file transfer components? (y/n) [y]: " install_core
install_core=${install_core:-y}
read -p "Install optional VPN support (OpenVPN)? (y/n) [n]: " install_vpn
install_vpn=${install_vpn:-n}
read -p "Install optional VoIP support (Mumble)? (y/n) [n]: " install_voip
install_voip=${install_voip:-n}

# Update package lists
if [[ "$platform" == "termux" ]]; then
    pkg update
else
    sudo apt-get update
fi

# Install core dependencies if requested
if [[ "$install_core" == [Yy]* ]]; then
    echo "Installing core dependencies: $DEP_PACKAGES"
    $PKG_INSTALL $DEP_PACKAGES
    # If on Termux, openssh includes sshd, consider starting it if needed:
    if [[ "$platform" == "termux" ]]; then
        # Termux: ensure sshd keys are generated and sshd started on demand
        if [[ ! -f "$PREFIX/etc/ssh/ssh_host_rsa_key" ]]; then
            ssh-keygen -f $PREFIX/etc/ssh/ssh_host_rsa_key -N '' -t rsa
        fi
        echo "To start the SSH server on Termux (for incoming connections), run: sshd"
    else
        # On Kali/other, ensure SSH service is enabled
        echo "Ensure SSH server is running for incoming connections (if needed) on this machine."
    fi
fi

# Install VPN support if requested
if [[ "$install_vpn" == [Yy]* ]]; then
    echo "Installing VPN support (OpenVPN)..."
    $PKG_INSTALL $VPN_PACKAGE
    # Generate a static key for OpenVPN
    mkdir -p config
    openvpn --genkey --secret config/static.key
    # Create a sample OpenVPN config
    cat > config/p2p_vpn.conf <<EOF
# Peer-to-Peer OpenVPN configuration (static key)
dev tun
ifconfig 10.8.0.1 10.8.0.2
secret static.key
port 1194
proto udp
# On one peer, run: sudo openvpn --config p2p_vpn.conf
# On the other peer, run as client: sudo openvpn --config p2p_vpn.conf --remote <server_ip>
EOF
    echo "OpenVPN static key generated at config/static.key and sample config at config/p2p_vpn.conf."
    echo "Share static.key securely with your peer before starting the VPN."
fi

# Install VoIP (Mumble) if requested
if [[ "$install_voip" == [Yy]* ]]; then
    if [[ "$platform" == "kali" || "$platform" == "linux" ]]; then
        echo "Installing Mumble (VoIP client)..."
        $PKG_INSTALL $VOIP_PACKAGE
        echo "Mumble client installed. You may also install a Mumble server (murmur) if needed for voice calls."
        sudo apt-get install -y mumble-server
        # We could prompt to configure murmur here (like set password), but skip for brevity.
    else
        echo "Mumble voice chat is not directly supported on Termux without GUI."
    fi
fi

echo "Installation complete."
echo "Please review the README.md for usage instructions on how to configure keys and start a secure chat."
