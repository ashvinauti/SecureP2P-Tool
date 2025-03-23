# Secure P2P Communication Tool

This project provides a command-line tool for secure peer-to-peer communication, supporting real-time encrypted messaging and file transfers, with optional voice/video calls via Mumble. It is designed to run on Kali Linux and Termux (Android) environments without relying on any central server.

## Features

- **End-to-End Encrypted Chat & File Transfer:** Uses GPG for message and file encryption so only the intended peer can decrypt the content.
- **Secure Transport (SSH Tunnel):** Can tunnel connections through SSH for an added layer of security and to traverse firewalls&#8203;:contentReference[oaicite:8]{index=8}.
- **Peer-to-Peer Architecture:** Direct communication between peers with no central server&#8203;:contentReference[oaicite:9]{index=9}. Peers must exchange keys and connect directly (via IP or using VPN).
- **Optional VPN Integration:** Includes configuration for an OpenVPN peer-to-peer tunnel (with static key&#8203;:contentReference[oaicite:10]{index=10}) for cases where direct IP connectivity is not available or to add an encrypted network layer.
- **Optional Encrypted Voice/Video:** Integrates Mumble for voice/video. Mumble provides low-latency, encrypted voice communication&#8203;:contentReference[oaicite:11]{index=11}.
- **Cross-Platform Support:** Works on Kali Linux and Termux (Android). The installer script detects the platform and installs appropriate dependencies.
- **Strong Authentication:** Uses GPG public keys for encrypting messages and SSH keys for tunneling. All authentication is local with no central authority&#8203;:contentReference[oaicite:12]{index=12}.

## Installation

Run the provided `install.sh` script to install dependencies and set up the tool. You can choose which components to install (messaging, VPN, VoIP). For example:

```bash
$ chmod +x install.sh
$ ./install.sh
