import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, FileText, Loader, MessageSquare, Mic, Square } from 'lucide-react';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  documents?: any[];
  documentCount?: number;
}

interface ChatResponse {
  status: string;
  ai_response: string;
  documents: any[];
  relevant_documents: number;
  context_provided: boolean;
}

const ChatPreview: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognition = useRef<any>(null);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      recognition.current = new SpeechRecognition();
      recognition.current.continuous = false;
      recognition.current.interimResults = false;
      recognition.current.lang = 'en-US';

      recognition.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        setIsListening(false);
      };

      recognition.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load chat history from localStorage
  useEffect(() => {
    const savedMessages = localStorage.getItem('km-chat-history');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages).map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(parsed);
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
  }, []);

  // Save chat history
  const saveChatHistory = (newMessages: ChatMessage[]) => {
    localStorage.setItem('km-chat-history', JSON.stringify(newMessages));
  };

  const startListening = () => {
    if (recognition.current && !isListening) {
      setIsListening(true);
      recognition.current.start();
    }
  };

  const stopListening = () => {
    if (recognition.current && isListening) {
      recognition.current.stop();
      setIsListening(false);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const text = messageText || inputMessage.trim();
    if (!text || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: text,
      timestamp: new Date()
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch('https://km-orchestrator.azurewebsites.net/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text }),
      });

      const data: ChatResponse = await response.json();

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.ai_response || 'I received your message but encountered an issue generating a response.',
        timestamp: new Date(),
        documents: data.documents || [],
        documentCount: data.relevant_documents || 0
      };

      const updatedMessages = [...newMessages, assistantMessage];
      setMessages(updatedMessages);
      saveChatHistory(updatedMessages);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      const updatedMessages = [...newMessages, errorMessage];
      setMessages(updatedMessages);
      saveChatHistory(updatedMessages);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('km-chat-history');
  };

  const quickQuestions = [
    "What documents do you have about AI?",
    "Summarize recent uploads",
    "Search for machine learning papers",
    "What's in my knowledge base?"
  ];

  if (!isExpanded) {
    return (
      <div className="space-y-4">
        {/* Quick Start */}
        <div className="text-center">
          <button
            onClick={() => setIsExpanded(true)}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center space-x-2"
          >
            <MessageSquare className="w-5 h-5" />
            <span>Start AI Conversation</span>
          </button>
        </div>

        {/* Quick Questions */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-300">Quick Questions:</h4>
          {quickQuestions.slice(0, 2).map((question, index) => (
            <button
              key={index}
              onClick={() => {
                setIsExpanded(true);
                setTimeout(() => sendMessage(question), 100);
              }}
              className="w-full text-left text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 px-3 rounded border border-slate-600 transition-colors"
            >
              {question}
            </button>
          ))}
        </div>

        {/* Recent Activity */}
        {messages.length > 0 && (
          <div className="bg-slate-800 rounded-lg p-3 border border-slate-600">
            <h4 className="text-sm font-medium text-slate-300 mb-2">Last Conversation:</h4>
            <div className="text-xs text-slate-400">
              {messages[messages.length - 1]?.content.substring(0, 60)}...
            </div>
            <button
              onClick={() => setIsExpanded(true)}
              className="text-xs text-blue-400 hover:text-blue-300 mt-1"
            >
              Continue conversation →
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Chat Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bot className="w-5 h-5 text-blue-400" />
          <h3 className="font-medium text-white">AI Assistant</h3>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={clearChat}
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            Clear
          </button>
          <button
            onClick={() => setIsExpanded(false)}
            className="text-xs text-slate-400 hover:text-white transition-colors"
          >
            Minimize
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="bg-slate-800 rounded-lg border border-slate-600 h-64 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 ? (
            <div className="text-center text-slate-400 py-8">
              <Bot className="w-8 h-8 mx-auto mb-2 text-slate-500" />
              <p className="text-sm">Ask me anything about your knowledge base!</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-100'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.type === 'assistant' && (
                      <Bot className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                    )}
                    {message.type === 'user' && (
                      <User className="w-4 h-4 text-blue-200 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      
                      {message.documentCount && message.documentCount > 0 && (
                        <div className="mt-2 text-xs text-slate-300">
                          <div className="flex items-center space-x-1">
                            <FileText className="w-3 h-3" />
                            <span>Referenced {message.documentCount} documents</span>
                          </div>
                        </div>
                      )}
                      
                      <div className="text-xs text-slate-400 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-700 rounded-lg p-3 flex items-center space-x-2">
                <Loader className="w-4 h-4 animate-spin text-blue-400" />
                <span className="text-sm text-slate-300">AI is thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-600 p-3">
          <div className="flex space-x-2">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your documents..."
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={2}
                disabled={loading}
              />
            </div>
            
            <div className="flex flex-col space-y-1">
              {/* Voice Input Button */}
              {recognition.current && (
                <button
                  onClick={isListening ? stopListening : startListening}
                  className={`p-2 rounded-lg transition-colors ${
                    isListening
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                  }`}
                  title={isListening ? 'Stop recording' : 'Start voice input'}
                >
                  {isListening ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
              )}
              
              {/* Send Button */}
              <button
                onClick={() => sendMessage()}
                disabled={!inputMessage.trim() || loading}
                className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Questions */}
      {messages.length === 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-300">Try asking:</h4>
          <div className="grid grid-cols-1 gap-1">
            {quickQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => sendMessage(question)}
                className="text-left text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 px-3 rounded border border-slate-600 transition-colors"
                disabled={loading}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPreview;