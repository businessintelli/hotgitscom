import ChatInterface from './ChatInterface'

const ChatPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            AI Career Assistant
          </h1>
          <p className="text-lg text-gray-600">
            Get personalized career guidance and job search assistance powered by AI
          </p>
        </div>
        
        <ChatInterface />
      </div>
    </div>
  )
}

export default ChatPage

