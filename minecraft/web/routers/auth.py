from fastapi import APIRouter, Response, HTTPException, status, Depends
from schemas import LoginRequest
from services import AuthService, PlayerService, get_current_user

router = APIRouter(prefix="/api", tags=["authentication"])

@router.post("/login")
def login(login_data: LoginRequest, response: Response):
    username = login_data.username.strip()
    password = login_data.password
    
    user = PlayerService.get_user_by_username(username)
    
    # We retrieve the raw password hash from player database to verify
    if not user or not AuthService.verify_password(password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    # Generate token
    token = AuthService.create_jwt_token(username)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=43200,  # 12 hours
        samesite="lax"
    )
    
    return {"message": "Logged in successfully"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
