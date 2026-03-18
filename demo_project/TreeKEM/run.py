from delivery_service import DeliveryService

def main():
    ds = DeliveryService()

    user1 = "Bertram"
    user2 = "Harun"
    user3 = "Saba"
    
    ds.add_new_client(user1)
    ds.add_new_client(user2)
    ds.add_new_client(user3)

    ds.add_new_group(ds.get_user_id(user1))
    
    












if __name__ == "__main__":
    main()