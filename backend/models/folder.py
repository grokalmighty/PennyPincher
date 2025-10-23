class Folder:
    def __init__(self, folder_id, name, description="", icon="📁"):
        self.id = folder_id
        self.name = name
        self.description = description
        self.icon = icon
        self.accounts = []
    
    def add_account(self, account):
        self.accounts.append(account)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'account_count': len(self.accounts)
        }

    