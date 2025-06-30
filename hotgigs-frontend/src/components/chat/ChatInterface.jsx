import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../App'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Send, Bot, User, Lightbulb, Briefcase, FileText, TrendingUp, MessageCircle } from 'lucide-react'

const ChatInterface = () => {
  const { user } = useAuth()
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const messagesEndRef = useRef(null)

  // Initialize chat with welcome message and suggestions
  useEffect(() => {
    const welcomeMessage = {
      id: 1,
      type: 'ai',
      content: `Hello ${user?.firstName || 'there'}! 👋 I'm your AI career assistant. I'm here to help you with job searching, resume optimization, interview preparation, and career guidance. How can I assist you today?`,
      timestamp: new Date(),
      suggestions: user?.role === 'candidate' ? [
        'Help me optimize my resume',
        'Find matching jobs for my skills',
        'Prepare for upcoming interviews',
        'Analyze my job search progress'
      ] : [
        'Help me write a job description',
        'Find qualified candidates',
        'Improve my recruitment strategy',
        'Analyze hiring metrics'
      ]
    }
    
    setMessages([welcomeMessage])
    setSuggestions(welcomeMessage.suggestions)
  }, [user])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Simulate AI response
  const generateAIResponse = async (userMessage) => {
    setIsTyping(true)
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    let response = ''
    let newSuggestions = []
    
    const messageLower = userMessage.toLowerCase()
    
    if (messageLower.includes('resume') || messageLower.includes('cv')) {
      response = `I'd be happy to help you optimize your resume! Here are some key recommendations:

📝 **Content Optimization:**
• Tailor your resume to each job application
• Use action verbs and quantify achievements
• Include relevant keywords from job descriptions

🎯 **Structure & Format:**
• Keep it to 1-2 pages maximum
• Use a clean, professional layout
• Ensure consistent formatting throughout

💡 **Pro Tips:**
• Add a compelling professional summary
• Highlight your most relevant skills and experiences
• Include metrics and specific accomplishments

Would you like me to analyze your current resume or help with a specific section?`
      
      newSuggestions = [
        'Analyze my current resume',
        'Help with professional summary',
        'Optimize for specific job',
        'Review skills section'
      ]
    } else if (messageLower.includes('job') && (messageLower.includes('find') || messageLower.includes('search'))) {
      response = `Let me help you find the perfect job opportunities! 🎯

🔍 **Smart Job Matching:**
Based on your profile, I can recommend jobs that match your:
• Skills and experience level
• Preferred industries and locations
• Salary expectations and career goals

📊 **Current Market Insights:**
• ${Math.floor(Math.random() * 500) + 200} new jobs posted this week in your field
• Average response rate: 15-25% for well-matched applications
• Best application times: Tuesday-Thursday, 10-11 AM

🚀 **Optimization Tips:**
• Apply within 24-48 hours of job posting
• Customize your application for each role
• Follow up professionally after 1-2 weeks

Would you like me to show you the latest matching opportunities?`
      
      newSuggestions = [
        'Show me matching jobs',
        'Set up job alerts',
        'Improve my job search strategy',
        'Analyze application success rate'
      ]
    } else if (messageLower.includes('interview')) {
      response = `Great! Let me help you ace your upcoming interviews! 🌟

🎯 **Interview Preparation Checklist:**
• Research the company and role thoroughly
• Prepare STAR method examples for common questions
• Practice your elevator pitch and key achievements
• Prepare thoughtful questions to ask the interviewer

💼 **Common Questions to Prepare:**
• "Tell me about yourself"
• "Why are you interested in this role?"
• "Describe a challenging situation you overcame"
• "Where do you see yourself in 5 years?"

🔧 **Technical Preparation:**
• Review job-specific technical requirements
• Practice coding challenges or case studies
• Prepare portfolio examples if applicable

📋 **Day-of Tips:**
• Arrive 10-15 minutes early
• Bring multiple copies of your resume
• Dress appropriately for company culture
• Send a thank-you email within 24 hours

What type of interview are you preparing for?`
      
      newSuggestions = [
        'Practice common questions',
        'Technical interview prep',
        'Company research tips',
        'Mock interview session'
      ]
    } else if (messageLower.includes('skill') || messageLower.includes('learn')) {
      response = `Excellent! Continuous learning is key to career growth! 📚

🎯 **In-Demand Skills for ${new Date().getFullYear()}:**
• **Technical:** AI/ML, Cloud Computing, Data Analysis, Cybersecurity
• **Soft Skills:** Leadership, Communication, Problem-solving, Adaptability
• **Industry-Specific:** Based on your field and career goals

📈 **Learning Recommendations:**
• Online courses (Coursera, Udemy, LinkedIn Learning)
• Professional certifications in your field
• Hands-on projects and portfolio building
• Networking and industry events

💡 **Skill Gap Analysis:**
Based on your profile and target roles, I recommend focusing on:
• Advanced ${user?.role === 'candidate' ? 'technical skills' : 'recruitment tools'}
• Industry-specific knowledge
• Leadership and management capabilities

🚀 **Quick Wins:**
• Update your LinkedIn with new skills
• Add relevant projects to your portfolio
• Join professional communities and forums

What specific skills would you like to develop?`
      
      newSuggestions = [
        'Analyze my skill gaps',
        'Recommend learning paths',
        'Find relevant courses',
        'Update my skills profile'
      ]
    } else if (user?.role === 'recruiter' && (messageLower.includes('candidate') || messageLower.includes('hire'))) {
      response = `I'll help you find and attract top talent! 🎯

👥 **Candidate Sourcing Strategies:**
• Leverage AI-powered matching algorithms
• Use advanced search filters and keywords
• Tap into passive candidate networks
• Optimize job descriptions for better visibility

📊 **Current Talent Market:**
• ${Math.floor(Math.random() * 1000) + 500} qualified candidates in your target pool
• Average time-to-hire: 23-35 days
• Top candidate sources: LinkedIn (40%), Job boards (30%), Referrals (20%)

🔍 **Screening Best Practices:**
• Use structured interview processes
• Implement skills-based assessments
• Check cultural fit alongside technical skills
• Maintain consistent evaluation criteria

💡 **Attraction Strategies:**
• Highlight company culture and benefits
• Offer competitive compensation packages
• Provide clear career progression paths
• Showcase employee testimonials

What type of role are you looking to fill?`
      
      newSuggestions = [
        'Search for candidates',
        'Optimize job posting',
        'Improve screening process',
        'Analyze hiring metrics'
      ]
    } else {
      response = `I understand you're looking for assistance! I'm here to help with various aspects of your ${user?.role === 'candidate' ? 'job search and career development' : 'recruitment and hiring process'}.

🤖 **What I can help you with:**
${user?.role === 'candidate' ? `
• Resume and cover letter optimization
• Job search strategy and matching
• Interview preparation and practice
• Skill development recommendations
• Career planning and guidance
• Application tracking and analytics` : `
• Candidate sourcing and screening
• Job description optimization
• Interview process improvement
• Hiring analytics and insights
• Recruitment strategy development
• Talent pipeline management`}

💬 **How to get started:**
Simply ask me about any of these topics, or choose from the suggestions below. I'm designed to provide personalized, actionable advice based on your specific situation and goals.

What would you like to focus on today?`
      
      newSuggestions = user?.role === 'candidate' ? [
        'Optimize my job search',
        'Improve my resume',
        'Practice interviews',
        'Develop new skills'
      ] : [
        'Find better candidates',
        'Improve job postings',
        'Streamline hiring process',
        'Analyze recruitment data'
      ]
    }
    
    const aiMessage = {
      id: messages.length + 1,
      type: 'ai',
      content: response,
      timestamp: new Date(),
      suggestions: newSuggestions
    }
    
    setMessages(prev => [...prev, aiMessage])
    setSuggestions(newSuggestions)
    setIsTyping(false)
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return
    
    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setSuggestions([])
    
    await generateAIResponse(inputMessage)
  }

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card className="h-[600px] flex flex-col">
        <CardHeader className="border-b">
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-blue-600" />
            AI Career Assistant
            <Badge variant="secondary" className="ml-2">
              {user?.role === 'candidate' ? 'Job Seeker' : 'Recruiter'} Mode
            </Badge>
          </CardTitle>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col p-0">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {message.type === 'ai' && (
                      <Bot className="h-5 w-5 mt-0.5 text-blue-600" />
                    )}
                    {message.type === 'user' && (
                      <User className="h-5 w-5 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      <div className={`text-xs mt-1 ${
                        message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
                  <div className="flex items-center gap-2">
                    <Bot className="h-5 w-5 text-blue-600" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="border-t p-4">
              <div className="text-sm text-gray-600 mb-2 flex items-center gap-1">
                <Lightbulb className="h-4 w-4" />
                Suggested questions:
              </div>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="text-xs"
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          )}
          
          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your career or job search..."
                className="flex-1 resize-none border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="2"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
                className="px-4"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Quick Actions */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-blue-600" />
            <div>
              <h3 className="font-semibold">Resume Help</h3>
              <p className="text-sm text-gray-600">Optimize your resume</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center gap-3">
            <Briefcase className="h-8 w-8 text-green-600" />
            <div>
              <h3 className="font-semibold">Job Matching</h3>
              <p className="text-sm text-gray-600">Find perfect roles</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-purple-600" />
            <div>
              <h3 className="font-semibold">Career Growth</h3>
              <p className="text-sm text-gray-600">Plan your future</p>
            </div>
          </div>
        </Card>
        
        <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
          <div className="flex items-center gap-3">
            <MessageCircle className="h-8 w-8 text-orange-600" />
            <div>
              <h3 className="font-semibold">Interview Prep</h3>
              <p className="text-sm text-gray-600">Practice & improve</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default ChatInterface

