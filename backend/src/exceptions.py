from fastapi import HTTPException, status


class PostError(HTTPException):
    """Base exception for post-related errors"""
    pass


class PostNotFoundError(PostError):
    def __init__(self, post_id=None):
        message = "Post not found" if post_id is None else f"Post with id {post_id} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class PostCreationError(PostError):
    def __init__(self, error: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create post: {error}")


class UserError(HTTPException):
    """Base exception for user-related errors"""
    pass


class UserNotFoundError(UserError):
    def __init__(self, user_id=None):
        message = "User not found" if user_id is None else f"User with id {user_id} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class InvalidPasswordError(UserError):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")


class PasswordMismatchError(UserError):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match")


class AuthenticationError(HTTPException):
    def __init__(self, message: str = "Could not validate user"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)


# Legacy exception names for backwards compatibility
NotFoundException = PostNotFoundError
UnauthorizedException = AuthenticationError


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class CommentError(HTTPException):
    """Base exception for comment-related errors"""
    pass


class CommentNotFoundError(CommentError):
    def __init__(self, comment_id=None):
        message = "Comment not found" if comment_id is None else f"Comment with id {comment_id} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)
