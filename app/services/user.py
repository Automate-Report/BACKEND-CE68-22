
class UserService:

    def is_user_exist(self,email:str):
        users = self._read_json()

        for user in users:
            if user["email"] == email:
                return True
        
        return False


# สร้าง Instance ไว้ให้ Router เรียกใช้
user_service = UserService()