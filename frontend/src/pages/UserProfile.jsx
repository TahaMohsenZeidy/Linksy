import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../services/api'
import Layout from '../components/Layout'
import { 
  Mail, 
  Calendar, 
  Phone, 
  User, 
  Edit, 
  Settings, 
  Camera,
  MapPin,
  Link as LinkIcon,
  Heart,
  MessageCircle,
  Share2,
  Grid3x3,
  BookOpen,
  Loader2,
  Send,
  Trash2
} from 'lucide-react'

function UserProfile() {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [userPosts, setUserPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ posts: 0, likes: 0, comments: 0 })
  const [profilePictureUrl, setProfilePictureUrl] = useState(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)
  const [profilePictureUrls, setProfilePictureUrls] = useState({}) // Map user_id -> presigned URL
  const [postImageUrls, setPostImageUrls] = useState({}) // Map post_id -> presigned URL
  const [comments, setComments] = useState({}) // Map post_id -> array of comments
  const [showComments, setShowComments] = useState({}) // Map post_id -> boolean
  const [showCommentInput, setShowCommentInput] = useState({}) // Map post_id -> boolean
  const [showAllComments, setShowAllComments] = useState({}) // Map post_id -> boolean
  const [commentInputs, setCommentInputs] = useState({}) // Map post_id -> comment text
  const [postingComment, setPostingComment] = useState({}) // Map post_id -> boolean
  const [liking, setLiking] = useState({}) // Map post_id -> boolean
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deletingPost, setDeletingPost] = useState(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    fetchProfile()
    fetchUserPosts()
  }, [])

  useEffect(() => {
    if (profile?.profile_picture_url) {
      fetchProfilePictureUrl()
    } else {
      setProfilePictureUrl(null)
    }
  }, [profile?.profile_picture_url])

  const fetchProfile = async () => {
    try {
      const response = await api.get('/users/me')
      setProfile(response.data)
    } catch (error) {
      console.error('Failed to fetch profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchProfilePictureUrl = async () => {
    if (!profile?.profile_picture_url) {
      setProfilePictureUrl(null)
      return
    }
    
    try {
      const response = await api.get('/users/me/profile-picture-url')
      setProfilePictureUrl(response.data.url)
    } catch (error) {
      console.error('Failed to fetch profile picture URL:', error)
      // If it's a connection error, show a helpful message
      const errorMessage = error.response?.data?.detail || error.message
      if (errorMessage && (errorMessage.includes('Cannot connect') || errorMessage.includes('DNS'))) {
        console.warn('MinIO connection issue:', errorMessage)
        // Don't set to null, keep the profile_picture_url so user knows they have a picture
        // but we just can't display it right now
      } else {
        setProfilePictureUrl(null)
      }
    }
  }

  const handleCameraClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB')
      return
    }

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      // Don't set Content-Type header - axios will set it automatically with boundary for FormData
      // Remove the default Content-Type header for this request
      const response = await api.post('/users/me/profile-picture', formData, {
        headers: {
          'Content-Type': undefined, // Let axios set it automatically
        },
      })

      // Update profile with new data
      setProfile(response.data)
      
      // Fetch the presigned URL for the new picture
      if (response.data.profile_picture_url) {
        await fetchProfilePictureUrl()
      }

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('Failed to upload profile picture:', error)
      alert(error.response?.data?.detail || 'Failed to upload profile picture')
    } finally {
      setUploading(false)
    }
  }

  const fetchUserPosts = async () => {
    try {
      const response = await api.get('/posts/me')
      setUserPosts(response.data)
      // Calculate total likes and comments from all posts
      const totalLikes = response.data.reduce((sum, post) => sum + (post.like_count || 0), 0)
      const totalComments = response.data.reduce((sum, post) => sum + (post.comment_count || 0), 0)
      setStats({ 
        posts: response.data.length,
        likes: totalLikes,
        comments: totalComments
      })
      // Fetch profile picture URLs for posts
      fetchProfilePictureUrls(response.data)
      // Fetch post image URLs for posts that have images
      fetchPostImageUrls(response.data)
    } catch (error) {
      console.error('Failed to fetch user posts:', error)
      // Set defaults if error
      setStats({ 
        posts: 0,
        likes: 0,
        comments: 0
      })
    }
  }

  const fetchProfilePictureUrls = async (postsData) => {
    const usersWithPictures = postsData
      .filter(post => post.profile_picture_url)
      .map(post => ({ user_id: post.user_id, object_name: post.profile_picture_url }))
    
    const uniqueUsers = Array.from(
      new Map(usersWithPictures.map(u => [u.user_id, u])).values()
    )

    const urlPromises = uniqueUsers.map(async ({ user_id }) => {
      try {
        const response = await api.get(`/users/${user_id}/profile-picture-url`)
        return { user_id, url: response.data.url }
      } catch (error) {
        console.error(`Failed to fetch profile picture URL for user ${user_id}:`, error)
        return null
      }
    })

    const results = await Promise.all(urlPromises)
    const urlMap = {}
    results.forEach(result => {
      if (result) {
        urlMap[result.user_id] = result.url
      }
    })
    setProfilePictureUrls(urlMap)
  }

  const fetchPostImageUrls = async (postsData) => {
    // Get posts that have images
    const postsWithImages = postsData
      .filter(post => post.image_url)
      .map(post => ({ post_id: post.id }))
    
    // Fetch presigned URLs for each post image
    const urlPromises = postsWithImages.map(async ({ post_id }) => {
      try {
        const response = await api.get(`/posts/${post_id}/image-url`)
        return { post_id, url: response.data.url }
      } catch (error) {
        console.error(`Failed to fetch post image URL for post ${post_id}:`, error)
        return null
      }
    })

    const results = await Promise.all(urlPromises)
    const urlMap = {}
    results.forEach(result => {
      if (result) {
        urlMap[result.post_id] = result.url
      }
    })
    setPostImageUrls(urlMap)
  }

  const fetchComments = async (postId, showAll = false) => {
    try {
      const response = await api.get(`/comments/posts/${postId}`)
      const allComments = response.data
      
      const commentsToShow = showAll ? allComments : allComments.slice(0, 2)
      
      setComments(prev => ({
        ...prev,
        [postId]: commentsToShow
      }))
      
      if (showAll) {
        setShowAllComments(prev => ({ ...prev, [postId]: true }))
      }
      
      const usersWithPictures = commentsToShow
        .filter(comment => comment.profile_picture_url)
        .map(comment => ({ user_id: comment.user_id }))
      
      const uniqueUsers = Array.from(
        new Map(usersWithPictures.map(u => [u.user_id, u])).values()
      )

      const urlPromises = uniqueUsers.map(async ({ user_id }) => {
        try {
          const urlResponse = await api.get(`/users/${user_id}/profile-picture-url`)
          return { user_id, url: urlResponse.data.url }
        } catch (error) {
          return null
        }
      })

      const results = await Promise.all(urlPromises)
      const urlMap = {}
      results.forEach(result => {
        if (result) {
          urlMap[result.user_id] = result.url
        }
      })
      setProfilePictureUrls(prev => ({ ...prev, ...urlMap }))
    } catch (error) {
      console.error(`Failed to fetch comments for post ${postId}:`, error)
    }
  }

  const fetchAllComments = async (postId) => {
    await fetchComments(postId, true)
  }

  const showCommentsOnly = (postId, event) => {
    if (event) {
      event.stopPropagation()
      event.preventDefault()
    }
    
    setShowComments(prev => {
      const isCurrentlyOpen = prev[postId] || false
      if (!isCurrentlyOpen) {
        setTimeout(() => {
          if (!comments[postId]) {
            fetchComments(postId, false)
          }
        }, 0)
        setShowCommentInput(prev => ({ ...prev, [postId]: false }))
        return { ...prev, [postId]: true }
      }
      setShowCommentInput(prev => ({ ...prev, [postId]: false }))
      return prev
    })
  }

  const showCommentsWithInput = (postId, event) => {
    if (event) {
      event.stopPropagation()
      event.preventDefault()
    }
    
    setShowComments(prev => {
      const isCurrentlyOpen = prev[postId] || false
      if (!isCurrentlyOpen) {
        setTimeout(() => {
          if (!comments[postId]) {
            fetchComments(postId, false)
          }
        }, 0)
      }
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
    e.stopPropagation()
    const commentText = commentInputs[postId]?.trim()
    if (!commentText) return

    setPostingComment(prev => ({ ...prev, [postId]: true }))
    try {
      const response = await api.post(`/comments/posts/${postId}`, {
        content: commentText
      })
      
      const shouldShowAll = showAllComments[postId]
      await fetchComments(postId, shouldShowAll)
      
      setCommentInputs(prev => {
        const newState = { ...prev }
        delete newState[postId]
        return newState
      })
      
      setUserPosts(prev => prev.map(p => 
        p.id === postId 
          ? { ...p, comment_count: (p.comment_count || 0) + 1 }
          : p
      ))
      
      if (response.data.profile_picture_url) {
        try {
          const urlResponse = await api.get(`/users/${response.data.user_id}/profile-picture-url`)
          setProfilePictureUrls(prev => ({
            ...prev,
            [response.data.user_id]: urlResponse.data.url
          }))
        } catch (error) {
          console.error('Failed to fetch profile picture URL:', error)
        }
      }
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
      const wasLiked = userPosts.find(p => p.id === postId)?.is_liked || false
      const newLikeCount = wasLiked 
        ? (userPosts.find(p => p.id === postId)?.like_count || 0) - 1
        : (userPosts.find(p => p.id === postId)?.like_count || 0) + 1
      
      setUserPosts(prev => prev.map(p => 
        p.id === postId 
          ? { ...p, is_liked: !wasLiked, like_count: newLikeCount }
          : p
      ))
      
      // Update stats
      const totalLikes = userPosts.reduce((sum, post) => {
        if (post.id === postId) {
          return sum + newLikeCount
        }
        return sum + (post.like_count || 0)
      }, 0)
      setStats(prev => ({ ...prev, likes: totalLikes }))
    } catch (error) {
      console.error('Failed to toggle like:', error)
    } finally {
      setLiking(prev => ({ ...prev, [postId]: false }))
    }
  }

  const handleDeleteClick = (post) => {
    setDeletingPost(post)
    setShowDeleteModal(true)
  }

  const handleDeletePost = async () => {
    if (!deletingPost) return

    setDeleting(true)
    try {
      const response = await api.delete(`/posts/${deletingPost.id}`)
      if (response.status === 204 || response.status === 200) {
        setUserPosts(prev => prev.filter(post => post.id !== deletingPost.id))
        setStats(prev => ({ 
          ...prev, 
          posts: prev.posts - 1,
          likes: prev.likes - (deletingPost.like_count || 0),
          comments: prev.comments - (deletingPost.comment_count || 0)
        }))
        setShowDeleteModal(false)
        setDeletingPost(null)
      }
    } catch (error) {
      console.error('Failed to delete post:', error)
      alert(error.response?.data?.detail || 'Failed to delete post')
    } finally {
      setDeleting(false)
    }
  }

  const getInitial = (username) => {
    if (!username) return 'U'
    const firstChar = username.charAt(0).toUpperCase()
    return firstChar || 'U'
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="glass rounded-2xl p-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400"></div>
          </div>
        </div>
      </Layout>
    )
  }

  if (!profile) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="glass rounded-2xl p-8">
            <p className="text-white/60 text-lg">Failed to load profile</p>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout onCreatePost={() => {}}>
      <div className="max-w-4xl mx-auto">
        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-3xl p-8 mb-6"
        >
          <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
            {/* Profile Picture */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="relative"
            >
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-purple-400 via-pink-400 to-orange-400 flex items-center justify-center border-4 border-white/20 shadow-2xl overflow-hidden">
                {profilePictureUrl ? (
                  <img
                    src={profilePictureUrl}
                    alt={profile.username}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-white text-4xl font-bold">
                    {getInitial(profile.username)}
                  </span>
                )}
              </div>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleCameraClick}
                disabled={uploading}
                className="absolute bottom-0 right-0 p-3 glass-strong rounded-full border-2 border-white/30 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                title="Upload profile picture"
              >
                {uploading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Camera className="w-5 h-5 text-white" />
                )}
              </motion.button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </motion.div>

            {/* Profile Info */}
            <div className="flex-1 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-3 mb-4">
                <h1 className="text-3xl font-bold text-white">{profile.username}</h1>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 glass rounded-xl text-white/60 hover:text-white hover:bg-white/10 transition-all"
                  title="Edit Profile"
                >
                  <Edit className="w-5 h-5" />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 glass rounded-xl text-white/60 hover:text-white hover:bg-white/10 transition-all"
                  title="Settings"
                >
                  <Settings className="w-5 h-5" />
                </motion.button>
              </div>

              {/* Stats */}
              <div className="flex items-center justify-center md:justify-start gap-6 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{stats.posts}</div>
                  <div className="text-sm text-white/60">Posts</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{stats.likes}</div>
                  <div className="text-sm text-white/60">Likes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{stats.comments}</div>
                  <div className="text-sm text-white/60">Comments</div>
                </div>
              </div>

              {/* User Details */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-white/80">
                  <User className="w-4 h-4" />
                  <span className="text-sm">{profile.username}</span>
                </div>
                <div className="flex items-center gap-2 text-white/80">
                  <Mail className="w-4 h-4" />
                  <span className="text-sm">{profile.email}</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Content Tabs */}
        <div className="flex items-center gap-2 mb-6">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 glass-strong rounded-xl p-4 flex items-center justify-center gap-2 text-white font-semibold"
          >
            <Grid3x3 className="w-5 h-5" />
            <span>Posts</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 glass rounded-xl p-4 flex items-center justify-center gap-2 text-white/60 hover:text-white hover:bg-white/10 transition-all"
          >
            <BookOpen className="w-5 h-5" />
            <span>Saved</span>
          </motion.button>
        </div>

        {/* User Posts */}
        {userPosts.length > 0 ? (
          <div className="space-y-6">
            <AnimatePresence>
              {userPosts.map((post, index) => (
                <motion.div
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  onClick={(e) => {
                    // Close comments if clicking outside the comments section
                    if (!e.target.closest('[data-comments-section]') && 
                        !e.target.closest('button[data-comment-button]')) {
                      closeComments(post.id)
                    }
                  }}
                  className="glass rounded-3xl p-6 glass-hover"
                >
                  {/* Post Header */}
                  <div className="flex items-center justify-between mb-4">
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
                        onClick={() => {
                          // Edit functionality can be added here
                        }}
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
                  
                  {/* Like/Comment Counts */}
                  <div className="flex items-center gap-4 mb-4 pb-4 border-b border-white/10">
                    <div className="flex items-center gap-2 text-white/60 text-sm">
                      <Heart className={`w-4 h-4 ${post.is_liked ? 'fill-red-400 text-red-400' : ''}`} />
                      <span>{post.like_count || 0}</span>
                    </div>
                    <button
                      data-comment-button
                      onClick={(e) => showCommentsOnly(post.id, e)}
                      className="flex items-center gap-2 text-white/60 hover:text-blue-400 transition-colors text-sm"
                    >
                      <MessageCircle className="w-4 h-4" />
                      <span>{post.comment_count || 0}</span>
                    </button>
                  </div>
                  
                  {/* Like, Comment, and Share buttons */}
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
                      />
                      <span className="text-sm">{post.is_liked ? 'Liked' : 'Like'}</span>
                    </motion.button>
                    <motion.button
                      data-comment-button
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
                      onClick={(e) => e.stopPropagation()}
                      onMouseDown={(e) => e.stopPropagation()}
                      className="mt-4 pt-4 border-t border-white/10"
                    >
                      {/* Comment Input */}
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
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass rounded-2xl p-12 text-center"
          >
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center">
              <Grid3x3 className="w-10 h-10 text-white" />
            </div>
            <p className="text-white/60 text-lg mb-2">No posts yet</p>
            <p className="text-white/40 text-sm">Start sharing your thoughts with the world!</p>
          </motion.div>
        )}

        {/* Delete Post Modal */}
        <AnimatePresence>
          {showDeleteModal && deletingPost && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
              onClick={() => setShowDeleteModal(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="glass-strong rounded-3xl p-8 w-full max-w-md shadow-2xl"
              >
                <h2 className="text-2xl font-bold text-white mb-4">Delete Post</h2>
                <p className="text-white/70 mb-6">Are you sure you want to delete this post? This action cannot be undone.</p>
                <div className="flex gap-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowDeleteModal(false)}
                    className="flex-1 glass rounded-xl py-3 text-white font-semibold hover:bg-white/20 transition-all"
                  >
                    Cancel
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleDeletePost}
                    disabled={deleting}
                    className="flex-1 glass rounded-xl py-3 text-red-400 font-semibold hover:bg-red-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {deleting ? 'Deleting...' : 'Delete'}
                  </motion.button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Layout>
  )
}

export default UserProfile

