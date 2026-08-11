from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas import UserResponse, ChangePasswordRequest, ResetRequest
from services import PlayerService, ResetRequestService, get_current_user

router = APIRouter(prefix="/api", tags=["users"])

@router.get("/users", response_model=List[UserResponse])
def list_users(current_user: dict = Depends(get_current_user)):
    players = PlayerService.list_all_users()
    
    # Post-process for users who are not admins (mask email addresses)
    for p in players:
        if current_user["role"] != "admin" and p["username"].lower() != current_user["username"].lower():
            p["email"] = "••••@••••.•••" if p.get("email") else None
            
    return players

@router.post("/users/change-password")
def change_password(req: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    user = PlayerService.get_user_by_username(current_user["username"])
    if not user or not PlayerService.AuthService.verify_password(req.old_password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    PlayerService.update_password(current_user["username"], req.new_password)
    return {"message": "Password updated successfully"}

@router.post("/reset-request")
def request_password_reset(req: ResetRequest):
    username = req.username.strip()
    user = PlayerService.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Player username not found")
        
    ResetRequestService.create_request(username)
    return {"message": "Password reset request submitted. Please notify an administrator."}
