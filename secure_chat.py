#!/usr/bin/env python3
"""
Secure P2P Chat Tool - provides encrypted chat and file transfer between two peers.
Usage:
  Run one peer with --listen and another with --connect, specifying peer IP/port and peer's GPG key ID.
  Example: python3 secure_chat.py --listen --port 9000 --peer-key partner@example.com
           python3 secure_chat.py --connect 192.168.1.5 --port 9000 --peer-key partner@example.com

This tool uses GPG for encryption and decryption of messages, and a TCP socket for transport.
It supports IPv4 and IPv6. For additional security, use an SSH tunnel or VPN as described in README.
"""
import socket
import subprocess
import threading
import sys
import os

# Placeholder variables that may be set via command-line arguments or environment
PEER_ADDRESS = None
LISTEN_MODE = False
PORT = 9000
PEER_GPG_ID = None  # GPG identifier (e.g., key ID or email) of the peer's public key

# Parse command-line arguments
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] in ("--listen", "-l"):
        LISTEN_MODE = True
    elif args[i] in ("--connect", "-c"):
        if i + 1 < len(args):
            PEER_ADDRESS = args[i+1]
            i += 1
        else:
            print("Error: --connect requires an address")
            sys.exit(1)
    elif args[i] in ("--port", "-p"):
        if i + 1 < len(args):
            PORT = int(args[i+1])
            i += 1
        else:
            print("Error: --port requires a port number")
            sys.exit(1)
    elif args[i] in ("--peer-key", "-r"):
        if i + 1 < len(args):
            PEER_GPG_ID = args[i+1]
            i += 1
        else:
            print("Error: --peer-key requires a key identifier")
            sys.exit(1)
    else:
        print(f"Unknown argument: {args[i]}")
        sys.exit(1)
    i += 1

if not LISTEN_MODE and PEER_ADDRESS is None:
    print("Usage: secure_chat.py --listen [--port X] --peer-key <id>\n"
          "   or: secure_chat.py --connect <address> [--port X] --peer-key <id>\n")
    sys.exit(0)

# If peer GPG key identifier is not provided via arguments, check environment variable
if PEER_GPG_ID is None:
    PEER_GPG_ID = os.environ.get("PEER_GPG_ID")
if PEER_GPG_ID is None:
    print("Error: Peer GPG key identifier not specified. Use --peer-key or set PEER_GPG_ID.")
    sys.exit(1)

# Define helper functions for encryption and decryption using GPG
def encrypt_message(plain_text):
    """
    Encrypt a plaintext string using GPG with the recipient's public key.
    Returns the ASCII-armored encrypted text as bytes, or None on failure.
    """
    try:
        proc = subprocess.run(
            ["gpg", "--encrypt", "--armor", "-r", PEER_GPG_ID],
            input=plain_text.encode('utf-8'),
            capture_output=True, check=True
        )
        return proc.stdout  # encrypted text in ASCII-armored format
    except subprocess.CalledProcessError as e:
        # GPG failed (e.g., missing public key)
        sys.stderr.write("Encryption error: " + e.stderr.decode('utf-8') + "\n")
        return None

def decrypt_message(cipher_text_bytes):
    """
    Decrypt an ASCII-armored ciphertext using GPG.
    Returns the plaintext as a string, or None if decryption fails.
    """
    try:
        proc = subprocess.run(
            ["gpg", "--decrypt"],
            input=cipher_text_bytes,
            capture_output=True, check=True
        )
        return proc.stdout.decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError as e:
        sys.stderr.write("Decryption error: " + e.stderr.decode('utf-8') + "\n")
        return None

# Set up socket (IPv6 if address contains ':', else IPv4)
family = socket.AF_INET6 if (PEER_ADDRESS and ":" in PEER_ADDRESS) else socket.AF_INET
sock = socket.socket(family, socket.SOCK_STREAM)

if LISTEN_MODE:
    # Bind and listen for incoming connection
    bind_host = '::' if sock.family == socket.AF_INET6 else ''  # '' binds INADDR_ANY for IPv4
    sock.bind((bind_host, PORT))
    sock.listen(1)
    print(f"Listening for incoming peer connection on port {PORT}...")
    conn, addr = sock.accept()
    print(f"Peer connected from {addr}")
    connection = conn
else:
    # Connect to the peer's address and port
    target_host = PEER_ADDRESS
    print(f"Connecting to {target_host}:{PORT} ...")
    sock.connect((target_host, PORT))
    print("Connected to peer.")
    connection = sock

# Thread function to receive and decrypt incoming messages
def receive_thread_func():
    while True:
        try:
            data = connection.recv(4096)
        except Exception as e:
            sys.stderr.write(f"Socket receive error: {e}\n")
            break
        if not data:
            # Connection closed by peer
            print("\n[Connection closed by peer]")
            break
        # Attempt to interpret incoming data
        text = None
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = None
        if text and text.startswith("FILE:"):
            # Handle incoming file transfer
            # Expected format: "FILE:<filename>:\n<ASCII armored data>..."
            header, sep, armored = text.partition("\n")
            filename = "received_file"
            header_parts = header.split(":", 2)
            if len(header_parts) >= 2:
                filename = header_parts[1]
            # If the armored data did not come in one chunk, we may need to receive more.
            if armored == "" and sep == "\n":
                # Continue receiving until EOF of PGP message (not fully implemented for brevity)
                more_data = connection.recv(65536)
                armored = more_data.decode('utf-8') if more_data else ""
            cipher_bytes = data[len(header)+1:]  # bytes after the header and newline
            try:
                # Decrypt file content and save to filename
                proc = subprocess.run(
                    ["gpg", "--decrypt", "-o", filename],
                    input=cipher_bytes, capture_output=True, check=True
                )
                print(f"\n[File received and saved as {filename}]")
            except subprocess.CalledProcessError as e:
                sys.stderr.write("File decryption error: " + e.stderr.decode('utf-8') + "\n")
        else:
            # Handle incoming text message
            plain = decrypt_message(data)
            if plain is not None:
                print(f"\nPeer: {plain}")
            else:
                print("[Could not decrypt incoming message]")
    try:
        connection.close()
    except:
        pass
    os._exit(0)  # terminate the program when connection is lost

# Start receiver thread
recv_thread = threading.Thread(target=receive_thread_func, daemon=True)
recv_thread.start()

# Main loop for sending user messages
try:
    while True:
        user_input = input()
        if not user_input:
            continue
        if user_input.strip().lower() == "/quit":
            print("Closing connection...")
            break
        if user_input.startswith("/send"):
            # User wants to send a file
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: /send <filepath>")
                continue
            filepath = parts[1]
            if not os.path.isfile(filepath):
                print(f"File not found: {filepath}")
                continue
            try:
                with open(filepath, "rb") as f:
                    file_data = f.read()
            except Exception as e:
                print(f"Failed to read file: {e}")
                continue
            try:
                proc = subprocess.run(
                    ["gpg", "--encrypt", "--armor", "-r", PEER_GPG_ID],
                    input=file_data, capture_output=True, check=True
                )
                encrypted_data = proc.stdout
            except subprocess.CalledProcessError as e:
                sys.stderr.write("Encryption error (file): " + e.stderr.decode('utf-8') + "\n")
                continue
            header = f"FILE:{os.path.basename(filepath)}:\n".encode('utf-8')
            try:
                connection.sendall(header + encrypted_data)
                print(f"[Sent file: {filepath}]")
            except Exception as e:
                print(f"File send failed: {e}")
                break
        else:
            # Send a normal text message
            cipher_bytes = encrypt_message(user_input)
            if cipher_bytes is None:
                print("Failed to encrypt message. Not sent.")
            else:
                try:
                    connection.sendall(cipher_bytes)
                except Exception as e:
                    print(f"Message send failed: {e}")
                    break
except (EOFError, KeyboardInterrupt):
    print("\nExiting chat...")
finally:
    try:
        connection.close()
    except:
        pass
