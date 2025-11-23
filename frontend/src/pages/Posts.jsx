import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'
import { Heart, MessageCircle, Send, X, Edit, Trash2, Share2 } from 'lucide-react'
import Layout from '../components/Layout'

function Posts() {
  const { user } = useAuth()
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [editingPost, setEditingPost] = useState(null)
  const [deletingPost, setDeletingPost] = useState(null)
  const [editPostTitle, setEditPostTitle] = useState('')
  const [editPostContent, setEditPostContent] = useState('')
  const [newPostTitle, setNewPostTitle] = useState('')
  const [newPost, setNewPost] = useState('')
  const [newPostImage, setNewPostImage] = useState(null)
  const [newPostImagePreview, setNewPostImagePreview] = useState(null)
  const [creating, setCreating] = useState(false)
  const [postImageUrls, setPostImageUrls] = useState({}) // Map post_id -> presigned URL
  const [updating, setUpdating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const [profilePictureUrls, setProfilePictureUrls] = useState({}) // Map user_id -> presigned URL
  const [comments, setComments] = useState({}) // Map post_id -> array of comments
  const [showComments, setShowComments] = useState({}) // Map post_id -> boolean
  const [showCommentInput, setShowCommentInput] = useState({}) // Map post_id -> boolean (whether to show input box)
  const [showAllComments, setShowAllComments] = useState({}) // Map post_id -> boolean (whether to show all comments)
  const [commentInputs, setCommentInputs] = useState({}) // Map post_id -> comment text
  const [postingComment, setPostingComment] = useState({}) // Map post_id -> boolean
  const [liking, setLiking] = useState({}) // Map post_id -> boolean

  useEffect(() => {
    fetchPosts()
  }, [])


  const fetchPosts = async () => {
    try {
      const response = await api.get('/posts/')
      setPosts(response.data)
      // Fetch profile picture URLs for posts that have profile pictures
      fetchProfilePictureUrls(response.data)
      // Fetch post image URLs for posts that have images
      fetchPostImageUrls(response.data)
    } catch (error) {
      // Silently handle error - posts will remain empty
    } finally {
      setLoading(false)
    }
  }

  const fetchProfilePictureUrls = async (postsData) => {
    // Get unique user IDs that have profile pictures
    const usersWithPictures = postsData
      .filter(post => post.profile_picture_url)
      .map(post => ({ user_id: post.user_id, object_name: post.profile_picture_url }))
    
    // Remove duplicates by user_id
    const uniqueUsers = Array.from(
      new Map(usersWithPictures.map(u => [u.user_id, u])).values()
    )

    // Use proxy endpoints directly (bypasses CORS issues)
    const urlMap = {}
    uniqueUsers.forEach(({ user_id }) => {
      // Use the proxy endpoint instead of presigned URLs
      urlMap[user_id] = `/api/storage/users/${user_id}/profile-picture`
    })
    setProfilePictureUrls(urlMap)
  }

  const fetchPostImageUrls = async (postsData) => {
    // Get posts that have images
    const postsWithImages = postsData
      .filter(post => post.image_url)
      .map(post => ({ post_id: post.id }))
    
    // Use proxy endpoints directly (bypasses CORS issues)
    const urlMap = {}
    postsWithImages.forEach(({ post_id }) => {
      // Use the proxy endpoint instead of presigned URLs
      urlMap[post_id] = `/api/storage/posts/${post_id}/image`
    })
    setPostImageUrls(urlMap)
  }

  const handleCreatePost = async (e) => {
    e.preventDefault()
    if (!newPost.trim() || !newPostTitle.trim()) return

    setCreating(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('title', newPostTitle)
      formData.append('content', newPost)
      if (newPostImage) {
        formData.append('image', newPostImage)
      }

      const response = await api.post('/posts/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setPosts([response.data, ...posts])
      
      // Use proxy endpoints directly for new post images
      if (response.data.profile_picture_url) {
        setProfilePictureUrls(prev => ({
          ...prev,
          [response.data.user_id]: `/api/storage/users/${response.data.user_id}/profile-picture`
        }))
      }
      
      if (response.data.image_url) {
        setPostImageUrls(prev => ({
          ...prev,
          [response.data.id]: `/api/storage/posts/${response.data.id}/image`
        }))
      }
      
      setNewPostTitle('')
      setNewPost('')
      setNewPostImage(null)
      setNewPostImagePreview(null)
      setShowCreateModal(false)
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create post')
    } finally {
      setCreating(false)
    }
  }

  const handleImageChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB')
      return
    }

    setNewPostImage(file)
    
    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setNewPostImagePreview(reader.result)
    }
    reader.readAsDataURL(file)
  }

  const handleEditPost = (post) => {
    setEditingPost(post)
    setEditPostTitle(post.title)
    setEditPostContent(post.content)
    setShowEditModal(true)
    setError('')
  }

  const handleUpdatePost = async (e) => {
    e.preventDefault()
    if (!editPostContent.trim() || !editPostTitle.trim()) return

    setUpdating(true)
    setError('')

    try {
      const response = await api.put(`/posts/${editingPost.id}`, {
        title: editPostTitle,
        content: editPostContent,
      })
      
      // Update the post in the list
      setPosts(posts.map(post => 
        post.id === editingPost.id ? response.data : post
      ))
      
      setShowEditModal(false)
      setEditingPost(null)
      setEditPostTitle('')
      setEditPostContent('')
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to update post')
    } finally {
      setUpdating(false)
    }
  }

  const handleDeleteClick = (post) => {
    setDeletingPost(post)
    setShowDeleteModal(true)
    setError('')
  }

  const handleDeletePost = async () => {
    if (!deletingPost) return

    setDeleting(true)
    setError('')

    try {
      const response = await api.delete(`/posts/${deletingPost.id}`)
      
      // Only remove from list if delete was successful (204 No Content)
      if (response.status === 204 || response.status === 200) {
        setPosts(posts.filter(post => post.id !== deletingPost.id))
        setShowDeleteModal(false)
        setDeletingPost(null)
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete post'
      setError(errorMessage)
      // Don't remove from list if delete failed
    } finally {
      setDeleting(false)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Get first letter for profile picture
  const getInitial = (username) => {
    if (!username) return 'U'
    // Get first letter, handling usernames like "john.doe" -> "J"
    const firstChar = username.charAt(0).toUpperCase()
    return firstChar || 'U'
  }

  const fetchComments = async (postId, showAll = false) => {
    try {
      const response = await api.get(`/comments/posts/${postId}`)
      const allComments = response.data
      
      // If not showing all, only take top 2 comments
      const commentsToShow = showAll ? allComments : allComments.slice(0, 2)
      
      setComments(prev => ({
        ...prev,
        [postId]: commentsToShow
      }))
      
      // Update showAllComments state
      if (showAll) {
        setShowAllComments(prev => ({ ...prev, [postId]: true }))
      }
      
      // Fetch profile picture URLs for comment authors
      const usersWithPictures = commentsToShow
        .filter(comment => comment.profile_picture_url)
        .map(comment => ({ user_id: comment.user_id }))
      
      const uniqueUsers = Array.from(
        new Map(usersWithPictures.map(u => [u.user_id, u])).values()
      )

      // Use proxy endpoints directly
      const urlMap = {}
      uniqueUsers.forEach(({ user_id }) => {
        urlMap[user_id] = `/api/storage/users/${user_id}/profile-picture`
      })
      setProfilePictureUrls(prev => ({ ...prev, ...urlMap }))
    } catch (error) {
      console.error(`Failed to fetch comments for post ${postId}:`, error)
    }
  }

  const fetchAllComments = async (postId) => {
    await fetchComments(postId, true)
  }

  const toggleComments = (postId, event, showInput = false) => {
    // Prevent event from bubbling up
    if (event) {
      event.stopPropagation()
      event.preventDefault()
    }
    
    setShowComments(prev => {
      const isCurrentlyOpen = prev[postId] || false
      const newState = { ...prev, [postId]: !isCurrentlyOpen }
      
      // If opening comments, fetch them
      if (!isCurrentlyOpen) {
        // Small delay to ensure state is updated
        setTimeout(() => {
          if (!comments[postId]) {
            fetchComments(postId, false) // Fetch only top 2 initially
          }
        }, 0)
        // Set whether to show input box
        setShowCommentInput(prev => ({ ...prev, [postId]: showInput }))
      } else {
        // Reset showAllComments and showCommentInput when closing
        setShowAllComments(prev => {
          const newState2 = { ...prev }
          delete newState2[postId]
          return newState2
        })
        setShowCommentInput(prev => {
          const newState2 = { ...prev }
          delete newState2[postId]
          return newState2
        })
      }
      
      return newState
    })
  }

  const showCommentsOnly = (postId, event) => {
    // Show comments without input box (read-only view)
    if (event) {
      event.stopPropagation()
      event.preventDefault()
    }
    
    setShowComments(prev => {
      const isCurrentlyOpen = prev[postId] || false
      if (!isCurrentlyOpen) {
        // If not open, open it and fetch comments
        setTimeout(() => {
          if (!comments[postId]) {
            fetchComments(postId, false) // Fetch only top 2 initially
          }
        }, 0)
        setShowCommentInput(prev => ({ ...prev, [postId]: false }))
        return { ...prev, [postId]: true }
      }
      // If already open, just ensure input is hidden
      setShowCommentInput(prev => ({ ...prev, [postId]: false }))
      return prev
    })
  }

  const showCommentsWithInput = (postId, event) => {
    // Show comments with input box (comment mode)
    if (event) {
      event.stopPropagation()
      event.preventDefault()
    }
    
    setShowComments(prev => {
      const isCurrentlyOpen = prev[postId] || false
      if (!isCurrentlyOpen) {
        // If not open, open it and fetch comments
        setTimeout(() => {
          if (!comments[postId]) {
            fetchComments(postId, false) // Fetch only top 2 initially
          }
        }, 0)
      }
      // Always show input box when Comment button is clicked
      setShowCommentInput(prev => ({ ...prev, [postId]: true }))
      return { ...prev, [postId]: true }
    })
  }

  const closeComments = (postId) => {
    setShowComments(prev => {
      const newState = { ...prev }
      delete newState[postId]
      return newState
    })
    setShowAllComments(prev => {
      const newState = { ...prev }
      delete newState[postId]
      return newState
    })
    setShowCommentInput(prev => {
      const newState = { ...prev }
      delete newState[postId]
      return newState
    })
  }

  const handleCommentSubmit = async (postId, e) => {
    e.preventDefault()
    e.stopPropagation() // Prevent closing the drawer
    const commentText = commentInputs[postId]?.trim()
    if (!commentText) return

    setPostingComment(prev => ({ ...prev, [postId]: true }))
    try {
      const response = await api.post(`/comments/posts/${postId}`, {
        content: commentText
      })
      
      // Refresh comments to show the new one (fetch all if showAllComments is true, otherwise top 2)
      const shouldShowAll = showAllComments[postId]
      await fetchComments(postId, shouldShowAll)
      
      // Clear the input
      setCommentInputs(prev => {
        const newState = { ...prev }
        delete newState[postId]
        return newState
      })
      
      // Update the post's comment count
      setPosts(prev => prev.map(p => 
        p.id === postId 
          ? { ...p, comment_count: (p.comment_count || 0) + 1 }
          : p
      ))
      
      // Use proxy endpoint directly for new comment author
      if (response.data.profile_picture_url) {
        setProfilePictureUrls(prev => ({
          ...prev,
          [response.data.user_id]: `/api/storage/users/${response.data.user_id}/profile-picture`
        }))
      }
      
      // Keep comments open after posting (don't close)
    } catch (error) {
      console.error('Failed to post comment:', error)
      alert(error.response?.data?.detail || 'Failed to post comment')
    } finally {
      setPostingComment(prev => ({ ...prev, [postId]: false }))
    }
  }

  const handleLike = async (postId) => {
    setLiking(prev => ({ ...prev, [postId]: true }))
    try {
      const response = await api.post(`/likes/posts/${postId}`)
      
      // Update the post's like count and is_liked status
      setPosts(prev => prev.map(p => 
        p.id === postId 
          ? { 
              ...p, 
              like_count: response.data.like_count,
              is_liked: response.data.is_liked
            }
          : p
      ))
    } catch (error) {
      console.error('Failed to toggle like:', error)
      alert(error.response?.data?.detail || 'Failed to toggle like')
    } finally {
      setLiking(prev => ({ ...prev, [postId]: false }))
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="glass rounded-2xl p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400"></div>
        </div>
      </div>
    )
  }

  return (
    <>
      <Layout onCreatePost={() => setShowCreateModal(true)}>
        <div className="max-w-4xl mx-auto p-4 md:p-8">
          {/* Posts List */}
          <div className="space-y-4">
          <AnimatePresence>
            {posts.map((post, index) => (
              <motion.div
                key={post.id}
                data-post-id={post.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
                onClick={(e) => {
                  // Close comments when clicking on the post card but outside comments section
                  const isCommentsSection = e.target.closest('[data-comments-section]')
                  const isCommentButton = e.target.closest('button')?.textContent?.includes('Comment')
                  if (!isCommentsSection && !isCommentButton && showComments[post.id]) {
                    closeComments(post.id)
                  }
                }}
                className="glass rounded-2xl p-6 glass-hover"
              >
                {/* Like and Comment counts at top */}
                <div className="flex items-center gap-4 mb-4 pb-3 border-b border-white/10">
                  <div className="flex items-center gap-2 text-white/70">
                    <Heart className="w-4 h-4" />
                    <span className="text-sm font-medium">{post.like_count || 0}</span>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={(e) => showCommentsOnly(post.id, e)}
                    className="flex items-center gap-2 text-white/70 hover:text-blue-400 transition-colors cursor-pointer"
                  >
                    <MessageCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">{post.comment_count || 0}</span>
                  </motion.button>
                </div>

                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {/* Profile Picture */}
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center border-2 border-white/20 shadow-lg overflow-hidden">
                      {profilePictureUrls[post.user_id] ? (
                        <img
                          src={profilePictureUrls[post.user_id]}
                          alt={post.username}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                      <span className="text-white text-sm font-semibold">
                        {getInitial(post.username)}
                      </span>
                      )}
                    </div>
                    {/* Username and Date */}
                    <div>
                      <p className="text-white font-medium text-sm mb-1">
                        {post.username || `user_${post.user_id}`}
                      </p>
                      <p className="text-white/50 text-xs">{formatDate(post.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleEditPost(post)}
                      className="p-2 glass rounded-lg text-white/60 hover:text-white hover:bg-white/20 transition-all"
                      title="Edit post"
                    >
                      <Edit className="w-4 h-4" />
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleDeleteClick(post)}
                      className="p-2 glass rounded-lg text-red-400/60 hover:text-red-400 hover:bg-red-500/20 transition-all"
                      title="Delete post"
                    >
                      <Trash2 className="w-4 h-4" />
                    </motion.button>
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">{post.title}</h3>
                <p className="text-white text-lg leading-relaxed mb-4">{post.content}</p>
                
                {/* Post Image */}
                {postImageUrls[post.id] && (
                  <div className="mb-4 rounded-xl overflow-hidden">
                    <img
                      src={postImageUrls[post.id]}
                      alt={post.title}
                      className="w-full h-auto max-h-96 object-cover"
                    />
                  </div>
                )}
                
                {/* Like, Comment, and Share buttons at bottom */}
                <div className="flex items-center gap-4 pt-4 border-t border-white/10">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleLike(post.id)}
                    disabled={liking[post.id]}
                    className={`flex items-center gap-2 transition-colors ${
                      post.is_liked 
                        ? 'text-red-400' 
                        : 'text-white/60 hover:text-red-400'
                    } ${liking[post.id] ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <Heart 
                      className={`w-5 h-5 ${post.is_liked ? 'fill-red-400 text-red-400' : ''}`}
                      style={post.is_liked ? { fill: 'currentColor' } : {}}
                    />
                    <span className="text-sm">{post.is_liked ? 'Liked' : 'Like'}</span>
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={(e) => showCommentsWithInput(post.id, e)}
                    className="flex items-center gap-2 text-white/60 hover:text-blue-400 transition-colors"
                  >
                    <MessageCircle className="w-5 h-5" />
                    <span className="text-sm">Comment</span>
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-2 text-white/60 hover:text-green-400 transition-colors"
                  >
                    <Share2 className="w-5 h-5" />
                    <span className="text-sm">Share</span>
                  </motion.button>
                </div>

                {/* Comments Section */}
                {showComments[post.id] && (
                  <motion.div
                    data-comments-section
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
                    onMouseDown={(e) => e.stopPropagation()} // Prevent closing when clicking inside
                    className="mt-4 pt-4 border-t border-white/10"
                  >
                    {/* Comment Input - Only show when Comment button was clicked */}
                    {showCommentInput[post.id] && (
                      <form onSubmit={(e) => handleCommentSubmit(post.id, e)} className="mb-4">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={commentInputs[post.id] || ''}
                          onChange={(e) => {
                            e.stopPropagation()
                            setCommentInputs(prev => ({
                              ...prev,
                              [post.id]: e.target.value
                            }))
                          }}
                          onFocus={(e) => e.stopPropagation()}
                          onClick={(e) => e.stopPropagation()}
                          placeholder="Write a comment..."
                          className="flex-1 glass rounded-xl px-4 py-2 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400/50 transition-all"
                        />
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          type="submit"
                          disabled={postingComment[post.id] || !commentInputs[post.id]?.trim()}
                          className="glass-strong rounded-xl px-4 py-2 text-white font-semibold hover:bg-white/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                          {postingComment[post.id] ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          ) : (
                            <Send className="w-4 h-4" />
                          )}
                        </motion.button>
                      </div>
                    </form>
                    )}

                    {/* Comments List */}
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {comments[post.id] && comments[post.id].length > 0 ? (
                        <>
                          {comments[post.id].map((comment) => (
                            <motion.div
                              key={comment.id}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              className="glass rounded-xl p-3"
                            >
                              <div className="flex items-start gap-3">
                                {/* Comment Author Profile Picture */}
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center border-2 border-white/20 shadow-lg overflow-hidden flex-shrink-0">
                                  {profilePictureUrls[comment.user_id] ? (
                                    <img
                                      src={profilePictureUrls[comment.user_id]}
                                      alt={comment.username}
                                      className="w-full h-full object-cover"
                                    />
                                  ) : (
                                    <span className="text-white text-xs font-semibold">
                                      {getInitial(comment.username)}
                                    </span>
                                  )}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <p className="text-white font-medium text-sm">
                                      {comment.username}
                                    </p>
                                    <p className="text-white/40 text-xs">
                                      {formatDate(comment.created_at)}
                                    </p>
                                  </div>
                                  <p className="text-white/80 text-sm">{comment.content}</p>
                                </div>
                              </div>
                            </motion.div>
                          ))}
                          {/* Show All Comments Button */}
                          {!showAllComments[post.id] && post.comment_count > 2 && (
                            <motion.button
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={(e) => {
                                e.stopPropagation()
                                fetchAllComments(post.id)
                              }}
                              className="w-full glass rounded-xl px-4 py-2 text-white/70 hover:text-white hover:bg-white/10 transition-all text-sm font-medium"
                            >
                              Show all {post.comment_count} comments
                            </motion.button>
                          )}
                        </>
                      ) : (
                        <p className="text-white/50 text-sm text-center py-4">No comments yet</p>
                      )}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {posts.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass rounded-2xl p-12 text-center"
            >
              <p className="text-white/60 text-lg">No posts yet. Be the first to share!</p>
            </motion.div>
          )}
          </div>
        </div>
      </Layout>

      {/* Create Post Modal */}
      <AnimatePresence>
        {showCreateModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
            onClick={() => setShowCreateModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-strong rounded-3xl p-8 w-full max-w-2xl shadow-2xl"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gradient">Create New Post</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleCreatePost} className="space-y-4">
                {error && (
                  <div className="glass rounded-xl p-4 border border-red-400/30 bg-red-500/10">
                    <p className="text-red-300 text-sm">{error}</p>
                  </div>
                )}

                <input
                  type="text"
                  value={newPostTitle}
                  onChange={(e) => setNewPostTitle(e.target.value)}
                  placeholder="Post title..."
                  className="w-full glass rounded-xl p-4 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400/50 focus:border-purple-400/50 transition-all"
                />

                <textarea
                  value={newPost}
                  onChange={(e) => setNewPost(e.target.value)}
                  placeholder="What's on your mind?"
                  rows={6}
                  className="w-full glass rounded-xl p-4 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400/50 focus:border-purple-400/50 transition-all resize-none"
                />

                {/* Image Upload */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-white/80">Add Image (Optional)</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="w-full glass rounded-xl p-2 border border-white/20 text-white/80 text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-500/50 file:text-white hover:file:bg-purple-500/70"
                  />
                  {newPostImagePreview && (
                    <div className="mt-2 rounded-xl overflow-hidden">
                      <img
                        src={newPostImagePreview}
                        alt="Preview"
                        className="w-full h-auto max-h-64 object-cover"
                      />
                    </div>
                  )}
                </div>

                <div className="flex gap-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 glass rounded-xl py-3 text-white font-semibold hover:bg-white/20 transition-all"
                  >
                    Cancel
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit"
                    disabled={creating || !newPost.trim() || !newPostTitle.trim()}
                    className="flex-1 glass-strong rounded-xl py-3 text-white font-semibold flex items-center justify-center gap-2 hover:bg-white/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {creating ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        Post
                      </>
                    )}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Post Modal */}
      <AnimatePresence>
        {showEditModal && editingPost && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
            onClick={() => setShowEditModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-strong rounded-3xl p-8 w-full max-w-2xl shadow-2xl"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gradient">Edit Post</h2>
                <button
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingPost(null)
                    setEditPostTitle('')
                    setEditPostContent('')
                  }}
                  className="text-white/60 hover:text-white transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleUpdatePost} className="space-y-4">
                {error && (
                  <div className="glass rounded-xl p-4 border border-red-400/30 bg-red-500/10">
                    <p className="text-red-300 text-sm">{error}</p>
                  </div>
                )}

                <input
                  type="text"
                  value={editPostTitle}
                  onChange={(e) => setEditPostTitle(e.target.value)}
                  placeholder="Post title..."
                  className="w-full glass rounded-xl p-4 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400/50 focus:border-purple-400/50 transition-all"
                />

                <textarea
                  value={editPostContent}
                  onChange={(e) => setEditPostContent(e.target.value)}
                  placeholder="What's on your mind?"
                  rows={6}
                  className="w-full glass rounded-xl p-4 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400/50 focus:border-purple-400/50 transition-all resize-none"
                />

                <div className="flex gap-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="button"
                    onClick={() => {
                      setShowEditModal(false)
                      setEditingPost(null)
                      setEditPostTitle('')
                      setEditPostContent('')
                    }}
                    className="flex-1 glass rounded-xl py-3 text-white font-semibold hover:bg-white/20 transition-all"
                  >
                    Cancel
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit"
                    disabled={updating || !editPostContent.trim() || !editPostTitle.trim()}
                    className="flex-1 glass-strong rounded-xl py-3 text-white font-semibold flex items-center justify-center gap-2 hover:bg-white/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updating ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        Update
                      </>
                    )}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {showDeleteModal && deletingPost && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
            onClick={() => {
              if (!deleting) {
                setShowDeleteModal(false)
                setDeletingPost(null)
              }
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-strong rounded-3xl p-8 w-full max-w-md shadow-2xl"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gradient">Delete Post</h2>
                <button
                  onClick={() => {
                    if (!deleting) {
                      setShowDeleteModal(false)
                      setDeletingPost(null)
                    }
                  }}
                  disabled={deleting}
                  className="text-white/60 hover:text-white transition-colors disabled:opacity-50"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                {error && (
                  <div className="glass rounded-xl p-4 border border-red-400/30 bg-red-500/10">
                    <p className="text-red-300 text-sm">{error}</p>
                  </div>
                )}

                <div className="glass rounded-xl p-4 border border-white/20">
                  <h3 className="text-white font-semibold mb-2">{deletingPost.title}</h3>
                  <p className="text-white/70 text-sm line-clamp-3">{deletingPost.content}</p>
                </div>

                <p className="text-white/80 text-center">
                  Are you sure you want to delete this post? This action cannot be undone.
                </p>

                <div className="flex gap-4 pt-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="button"
                    onClick={() => {
                      if (!deleting) {
                        setShowDeleteModal(false)
                        setDeletingPost(null)
                      }
                    }}
                    disabled={deleting}
                    className="flex-1 glass rounded-xl py-3 text-white font-semibold hover:bg-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Cancel
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleDeletePost}
                    disabled={deleting}
                    className="flex-1 glass-strong rounded-xl py-3 text-red-400 font-semibold flex items-center justify-center gap-2 hover:bg-red-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-red-400/30"
                  >
                    {deleting ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-400"></div>
                    ) : (
                      <>
                        <Trash2 className="w-5 h-5" />
                        Delete
                      </>
                    )}
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default Posts

