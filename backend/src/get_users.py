from .eagle import EaglDB

db = EaglDB()
users = db.get_all_users()

print('ID | Name | Email | Password | Role')
print('-' * 60)
for u in users:
    print(f"{u['id']} | {u['name']} | {u['email']} | {u['password']} | {u['role']}")
