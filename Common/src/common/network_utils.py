import struct

def send_big(sock, data_bytes):
    # Create a 4-byte header representing the length of the payload
    # '>I' means Big-Endian Unsigned Integer (Standard network byte order)
    header = struct.pack('>I', len(data_bytes))
    
    # 3. Send the header followed by the actual data using sendall
    # sendall ensures the entire buffer is sent over the network
    sock.sendall(header + data_bytes)


def recvall(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            # Socket was closed mid-transmission
            return None
        data.extend(packet)
    return data


def recv_big(sock):
    # 1. Read the 4-byte length header
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
        
    # 2. Unpack the header to find out how many bytes the JSON payload is
    msglen = struct.unpack('>I', raw_msglen)[0]
    
    # 3. Read exactly 'msglen' bytes from the socket
    raw_data = recvall(sock, msglen)
    if not raw_data:
        return None
        
    # 4. Decode the bytes back to string, then parse the JSON
    return raw_data