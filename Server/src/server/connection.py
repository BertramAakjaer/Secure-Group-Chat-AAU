import json

from common.utils import PackageType
from common.json_pcks import new_UUID_packet, from_json

from common.network_utils import recv_big, send_big


import server.group as group


clients = group.clients


# Thread that runs for each client
def handle_client(conn, addr, client_uuid):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    clients[client_uuid] = (conn, addr, None, None)  # Group and Username are empty 
    
    try:
        send_big(conn, new_UUID_packet(client_uuid))
    
        while True:
            try:
                data = recv_big(conn)
                
                # If no data, the client disconnected
                if not data:
                    break
                
                # Try to parse as JSON
                try:
                    json_data = from_json(data)
                    msg_type = json_data.get("Type")
                    msg_payload = json_data.get("Payload", {})
                    
                    match msg_type:
                        case PackageType.CREATE_GROUP.value:
                            group_name = msg_payload.get("group_name")
                            admin_uuid = msg_payload.get("admin_uuid")
                            group.create_group(group_name, admin_uuid)
                        
                        case PackageType.JOIN_GROUP.value:
                            group_uuid = msg_payload.get("group_uuid")
                            user_uuid = msg_payload.get("user_uuid")
                            pub_key_b64 = msg_payload.get("pub_key_b64")
                            group.request_join_group(group_uuid, user_uuid, pub_key_b64)
                        
                        case PackageType.JOIN_ACCEPTED.value:
                            group_uuid = msg_payload.get("group_uuid")
                            group_name = msg_payload.get("group_name")
                            welcome_data = msg_payload.get("welcome_data")
                            accepted_uuid = msg_payload.get("accepted_uuid")
                            
                            group.accept_join(group_uuid, accepted_uuid, client_uuid, welcome_data)
                        
                        case PackageType.COMMIT.value:
                            guid = msg_payload.get("guid")
                            commit_data = msg_payload.get("commit_data")
                            group.handle_commit(guid, commit_data, client_uuid)
                        
                        case PackageType.USER_INFO.value:
                            uuid = msg_payload.get("uuid")
                            username = msg_payload.get("username")
                            if uuid in clients:
                                clients[uuid] = (clients[uuid][0], clients[uuid][1], clients[uuid][2], username)
                                print(f"[USER INFO] {uuid} is {username}")
                        
                        case PackageType.MSG.value:
                            message = msg_payload.get("message")
                            sender_uuid = msg_payload.get("sender_uuid")
                            group_uuid = msg_payload.get("group_uuid")
                            epoch = msg_payload.get("epoch")
                            
                            # Check if it's an admin command
                            #if group.handle_admin_command(message, sender_uuid):
                            #    continue
                        
                            group.broadcast_to_group(group_uuid, message, sender_uuid, epoch)
                
                except json.JSONDecodeError:
                    # Plain text message (legacy)
                    print(f"[ERROR] decoding message from {addr} as JSON: {data.decode('utf-8')}")
                
            except ConnectionResetError:
                break
            
            except Exception as e:
                print(f"[ERROR] Connection lost with {addr}: {e}")
                break
    finally: # Cleanup
        print(f"[DISCONNECTED] {addr} disconnected.")
        group.remove_client(client_uuid)
        conn.close()