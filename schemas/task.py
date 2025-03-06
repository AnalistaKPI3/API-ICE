def taskEntity(item) -> dict:
    return {
        "id": str(item["id"]),
        "code": item["code"],
        "created_at": item["created_at"],
        "updated_at": item["updated_at"],
    }
    
    
def tasksEntity(entity) -> list:
    return [taskEntity(item) for item in entity]