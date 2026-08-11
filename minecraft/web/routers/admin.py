from fastapi import APIRouter, Form, HTTPException, Depends, status
from typing import List, Optional
from schemas import CreateUserRequest, RoleChangeRequest
from services import PlayerService, ResetRequestService, require_admin

router = APIRouter(prefix="", tags=["admin"])

@router.post("/api/users", status_code=status.HTTP_201_CREATED)
def create_user(req: CreateUserRequest, current_user: dict = Depends(require_admin)):
    username = req.username.strip()
    if not username or len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        
    res = PlayerService.create_user(
        username=username,
        password_raw=req.password,
        email=req.email,
        role=req.role
    )
    return {"message": f"Player {username} created successfully", "user": res}

@router.delete("/api/users/{username}")
def delete_user(username: str, current_user: dict = Depends(require_admin)):
    if username.lower() == current_user["username"].lower():
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
    PlayerService.delete_user(username)
    return {"message": f"Player {username} deleted successfully"}

@router.post("/api/users/{username}/role")
def change_role(username: str, req: RoleChangeRequest, current_user: dict = Depends(require_admin)):
    if username.lower() == current_user["username"].lower():
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    if req.role not in ["admin", "player"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'player'")
        
    PlayerService.update_role(username, req.role)
    return {"message": f"Role for {username} updated to {req.role}"}

@router.get("/api/admin/reset-requests")
def list_reset_requests(current_user: dict = Depends(require_admin)):
    return ResetRequestService.list_requests()

@router.post("/api/admin/reset-requests/{username}/resolve")
def resolve_reset_request(
    username: str, 
    action: str = Form(...), 
    new_password: Optional[str] = Form(None), 
    current_user: dict = Depends(require_admin)
):
    if action == "approve":
        if not new_password or len(new_password) < 5:
            raise HTTPException(status_code=400, detail="A valid new password is required to approve the reset")
            
        PlayerService.update_password(username, new_password)
        ResetRequestService.delete_request(username)
        return {"message": f"Password reset for {username} approved and updated."}
        
    elif action == "reject":
        ResetRequestService.delete_request(username)
        return {"message": f"Reset request for {username} rejected."}
        
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
