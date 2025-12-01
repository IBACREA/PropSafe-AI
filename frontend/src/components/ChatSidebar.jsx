import React, { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import LoadingSpinner from './LoadingSpinner'
import {
  PaperAirplaneIcon,
  SparklesIcon,
  ChevronRightIcon,
  ChevronLeftIcon,
} from '@heroicons/react/24/outline'

export default function ChatSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '¡Hola! Soy tu asistente para análisis de datos inmobiliarios. ¿En qué puedo ayudarte?',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadSuggestions()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadSuggestions = async () => {
    try {
      const response = await api.getSuggestions()
      setSuggestions(response.data)
    } catch (err) {
      // Si el endpoint no existe, usar sugerencias por defecto
      setSuggestions([
        '¿Cuál es el precio promedio en Bogotá?',
        'Muéstrame transacciones sospechosas',
        '¿Cuántas anomalías hay en total?',
        'Analiza las tendencias de fraude',
      ])
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await api.chatQuery({
        question: userMessage,
        top_k: 5,
        include_sources: true,
      })

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.data.answer,
          sources: response.data.sources,
          confidence: response.data.confidence,
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Lo siento, ocurrió un error. Por favor intenta nuevamente.',
          error: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion)
  }

  return (
    <>
      {/* Chat Dock - Always visible */}
      <div
        className={`fixed top-16 right-0 bottom-0 bg-white border-l border-gray-200 shadow-xl transition-all duration-300 ease-in-out z-30 ${
          isCollapsed ? 'w-12' : 'w-96'
        }`}
      >
        {/* Collapse/Expand Button */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -left-6 top-4 bg-primary-600 text-white p-1.5 rounded-l-lg shadow-lg hover:bg-primary-700 transition-colors"
          title={isCollapsed ? 'Expandir chat' : 'Colapsar chat'}
        >
          {isCollapsed ? (
            <ChevronLeftIcon className="h-4 w-4" />
          ) : (
            <ChevronRightIcon className="h-4 w-4" />
          )}
        </button>

        {!isCollapsed && (
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white px-4 py-3 flex items-center gap-2">
              <SparklesIcon className="h-5 w-5" />
              <div className="flex-1">
                <h2 className="font-bold text-base">Asistente IA</h2>
                <p className="text-xs text-primary-100">Siempre disponible</p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-gray-50">
              {messages.map((message, idx) => (
                <div
                  key={idx}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : message.error
                        ? 'bg-red-50 text-red-900 border border-red-200'
                        : 'bg-white text-gray-900 shadow-sm border border-gray-200'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>

                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <p className="text-xs text-gray-500 mb-1">Fuentes:</p>
                        <div className="space-y-1">
                          {message.sources.slice(0, 2).map((source, srcIdx) => (
                            <div
                              key={srcIdx}
                              className="text-xs text-gray-600 bg-gray-50 rounded p-1"
                            >
                              <div className="flex justify-between items-start">
                                <span className="flex-1 line-clamp-2">{source.content}</span>
                                <span className="ml-1 text-primary-600 font-medium text-[10px]">
                                  {(source.relevance_score * 100).toFixed(0)}%
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {message.confidence !== undefined && (
                      <div className="mt-1 text-xs text-gray-500">
                        Confianza: {(message.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white rounded-lg px-3 py-2 shadow-sm border border-gray-200">
                    <LoadingSpinner size="sm" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions */}
            {messages.length === 1 && suggestions.length > 0 && (
              <div className="px-4 py-3 bg-white border-t border-gray-200">
                <p className="text-xs text-gray-600 mb-2">Sugerencias:</p>
                <div className="flex flex-wrap gap-1.5">
                  {suggestions.slice(0, 3).map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="bg-white border-t border-gray-200 px-4 py-3">
              <form onSubmit={handleSubmit}>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Pregunta algo..."
                    disabled={loading}
                    className="flex-1 text-sm rounded-lg border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <PaperAirplaneIcon className="h-4 w-4" />
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Collapsed State */}
        {isCollapsed && (
          <div className="flex flex-col items-center py-4 gap-3">
            <SparklesIcon className="h-6 w-6 text-primary-600" />
            <div className="transform -rotate-90 whitespace-nowrap text-xs font-medium text-gray-600">
              Chat IA
            </div>
          </div>
        )}
      </div>
    </>
  )
}
