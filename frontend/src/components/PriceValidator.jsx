import React, { useState } from 'react'
import {
  CurrencyDollarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const MUNICIPIOS = [
  'BOGOTA', 'MEDELLIN', 'CALI', 'BARRANQUILLA', 'CARTAGENA',
  'CUCUTA', 'BUCARAMANGA', 'PEREIRA', 'MANIZALES', 'IBAGUE'
]

export default function PriceValidator() {
  const [formData, setFormData] = useState({
    municipio: 'BOGOTA',
    departamento: 'CUNDINAMARCA',
    valor_acto: '',
    area_construida: 85,
    area_terreno: 100,
    tipo_predio: 'urbano',
  })
  
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleValidate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await api.predictPrice({
        ...formData,
        valor_acto: parseFloat(formData.valor_acto),
        area_construida: parseFloat(formData.area_construida),
        area_terreno: parseFloat(formData.area_terreno),
      })
      
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al validar precio')
    } finally {
      setLoading(false)
    }
  }

  const getClassificationIcon = (clasificacion) => {
    switch (clasificacion) {
      case 'normal':
        return <CheckCircleIcon className="h-6 w-6 text-green-600" />
      case 'precaucion':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />
      case 'sospechoso':
        return <XCircleIcon className="h-6 w-6 text-red-600" />
      default:
        return null
    }
  }

  const getClassificationColor = (clasificacion) => {
    switch (clasificacion) {
      case 'normal':
        return 'bg-green-50 border-green-200'
      case 'precaucion':
        return 'bg-yellow-50 border-yellow-200'
      case 'sospechoso':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-primary-100">
        <div className="flex items-center gap-3">
          <SparklesIcon className="h-6 w-6 text-primary-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Validador Inteligente de Precios
            </h2>
            <p className="text-sm text-gray-600">
              IA entrenada con 100k transacciones reales
            </p>
          </div>
        </div>
      </div>

      <div className="p-6">
        <form onSubmit={handleValidate} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Municipio *
              </label>
              <select
                name="municipio"
                value={formData.municipio}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {MUNICIPIOS.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valor a Validar (COP) *
              </label>
              <input
                type="number"
                name="valor_acto"
                value={formData.valor_acto}
                onChange={handleChange}
                required
                placeholder="250000000"
                className="w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Área Construida (m²)
              </label>
              <input
                type="number"
                name="area_construida"
                value={formData.area_construida}
                onChange={handleChange}
                placeholder="85"
                className="w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !formData.valor_acto}
            className="w-full md:w-auto px-6 py-3 bg-primary-600 text-white font-semibold rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" />
                Analizando...
              </>
            ) : (
              <>
                <CurrencyDollarIcon className="h-5 w-5" />
                Validar Precio
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {result && (
          <div className={`mt-6 p-6 border-2 rounded-lg ${getClassificationColor(result.clasificacion)}`}>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                {getClassificationIcon(result.clasificacion)}
              </div>
              
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {result.mensaje}
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-4">
                  <div>
                    <p className="text-xs text-gray-600">Tu Precio</p>
                    <p className="text-lg font-bold text-gray-900">
                      ${(result.tu_precio / 1000000).toFixed(1)}M
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Precio Predicho</p>
                    <p className="text-lg font-bold text-primary-600">
                      ${(result.precio_predicho / 1000000).toFixed(1)}M
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Rango Normal</p>
                    <p className="text-sm font-medium text-gray-700">
                      ${(result.rango_normal.minimo / 1000000).toFixed(1)}M - 
                      ${(result.rango_normal.maximo / 1000000).toFixed(1)}M
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Desviación</p>
                    <p className={`text-lg font-bold ${
                      result.desviacion_porcentaje > 30 ? 'text-red-600' :
                      result.desviacion_porcentaje > 15 ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {result.desviacion_porcentaje.toFixed(1)}%
                    </p>
                  </div>
                </div>

                {/* Barra de progreso */}
                <div className="my-4">
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>Bajo</span>
                    <span>Normal</span>
                    <span>Alto</span>
                  </div>
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500" />
                  </div>
                  <div className="relative h-6">
                    <div 
                      className="absolute w-0.5 h-6 bg-gray-900"
                      style={{ 
                        left: `${Math.min(Math.max((result.tu_precio / result.rango_normal.maximo) * 100, 0), 100)}%`
                      }}
                    >
                      <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-gray-900 rounded-full" />
                    </div>
                  </div>
                </div>

                {/* Nivel de confianza */}
                <div className="flex items-center gap-2 text-sm text-gray-700 mb-4">
                  <span className="font-medium">Confianza del modelo:</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden max-w-xs">
                    <div 
                      className="h-full bg-primary-600"
                      style={{ width: `${result.score_confianza * 100}%` }}
                    />
                  </div>
                  <span className="font-semibold">{(result.score_confianza * 100).toFixed(0)}%</span>
                </div>

                {/* Recomendaciones */}
                {result.recomendaciones && result.recomendaciones.length > 0 && (
                  <div className="mt-4 p-4 bg-white border border-gray-200 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-2">
                      Recomendaciones:
                    </h4>
                    <ul className="space-y-2">
                      {result.recomendaciones.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                          <span className="text-primary-600 font-bold">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
