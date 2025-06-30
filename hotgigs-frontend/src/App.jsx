import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect, createContext, useContext } from 'react'
import './App.css'

// Import components
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import HomePage from './components/HomePage'
import LoginPage from './components/auth/LoginPage'
import RegisterPage from './components/auth/RegisterPage'
import DashboardPage from './components/dashboard/DashboardPage'
import JobsPage from './components/jobs/JobsPage'
import JobDetailsPage from './components/jobs/JobDetailsPage'
import ProfilePage from './components/profile/ProfilePage'
import MatchingPage from './components/matching/MatchingPage'
import AnalyticsPage from './components/analytics/AnalyticsPage'
import ChatPage from './components/chat/ChatPage'
import LoadingSpinner from './components/ui/LoadingSpinner'

// Auth Context
const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <LoadingSpinner />
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check for existing authentication on app load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('hotgigs_token')
        if (token) {
          // Verify token with backend
          const response = await fetch('http://localhost:5000/auth/verify', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })
          
          if (response.ok) {
            const userData = await response.json()
            setUser(userData.user)
          } else {
            localStorage.removeItem('hotgigs_token')
          }
        } else {
          // Set demo user for testing when no backend is available
          setUser({
            id: 1,
            email: 'candidate@demo.com',
            role: 'candidate',
            firstName: 'Demo',
            lastName: 'Candidate'
          })
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        localStorage.removeItem('hotgigs_token')
        // Set demo user for testing when backend is not available
        setUser({
          id: 1,
          email: 'candidate@demo.com',
          role: 'candidate',
          firstName: 'Demo',
          lastName: 'Candidate'
        })
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email, password) => {
    try {
      const response = await fetch('http://localhost:5000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      const data = await response.json()

      if (response.ok) {
        localStorage.setItem('hotgigs_token', data.access_token)
        setUser(data.user)
        return { success: true }
      } else {
        return { success: false, error: data.error || 'Login failed' }
      }
    } catch (error) {
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  const register = async (userData) => {
    try {
      const response = await fetch('http://localhost:5000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      })

      const data = await response.json()

      if (response.ok) {
        localStorage.setItem('hotgigs_token', data.access_token)
        setUser(data.user)
        return { success: true }
      } else {
        return { success: false, error: data.error || 'Registration failed' }
      }
    } catch (error) {
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  const logout = () => {
    localStorage.removeItem('hotgigs_token')
    setUser(null)
  }

  const authValue = {
    user,
    login,
    register,
    logout,
    loading
  }

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <AuthContext.Provider value={authValue}>
      <Router>
        <div className="min-h-screen bg-background flex flex-col">
          <Navbar />
          
          <main className="flex-1">
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<HomePage />} />
              <Route 
                path="/login" 
                element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} 
              />
              <Route 
                path="/register" 
                element={user ? <Navigate to="/dashboard" replace /> : <RegisterPage />} 
              />
              
              {/* Protected Routes */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/jobs" 
                element={
                  <ProtectedRoute>
                    <JobsPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/jobs/:id" 
                element={
                  <ProtectedRoute>
                    <JobDetailsPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/matching" 
                element={
                  <ProtectedRoute>
                    <MatchingPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/analytics" 
                element={
                  <ProtectedRoute>
                    <AnalyticsPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/chat" 
                element={
                  <ProtectedRoute>
                    <ChatPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          
          <Footer />
        </div>
      </Router>
    </AuthContext.Provider>
  )
}

export default App

