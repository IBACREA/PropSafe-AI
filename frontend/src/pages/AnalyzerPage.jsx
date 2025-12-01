import React, { useState } from 'react'
import { api } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import RiskBadge from '../components/RiskBadge'
import { CloudArrowUpIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

export default function AnalyzerPage() {
  const [activeTab, setActiveTab] = useState('single') // 'single' or 'batch'
  const [formData, setFormData] = useState({
    valor_acto: '',
    tipo_acto: 'compraventa',
    fecha_acto: new Date().toISOString().split('T')[0],
    departamento: '',
    municipio: '',
    tipo_predio: 'urbano',
    numero_intervinientes: 2,
    estado_folio: 'activo',
    area_terreno: '',
    area_construida: '',
  })
  const [result, setResult] = useState(null)
  const [batchResult, setBatchResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleSingleAnalysis = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const payload = {
        ...formData,
        valor_acto: parseFloat(formData.valor_acto),
        numero_intervinientes: parseInt(formData.numero_intervinientes),
        area_terreno: formData.area_terreno ? parseFloat(formData.area_terreno) : null,
        area_construida: formData.area_construida ? parseFloat(formData.area_construida) : null,
        fecha_acto: new Date(formData.fecha_acto).toISOString(),
      }

      const response = await api.analyzeTransaction(payload)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error analizando transacción')
    } finally {
      setLoading(false)
    }
  }

  const handleBatchUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    setError(null)
    setBatchResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.batchAnalyze(formData)
      setBatchResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error procesando archivo')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Analizador de Transacciones
        </h1>
        <p className="mt-2 text-gray-600">
          Analiza transacciones individuales o en lote para detectar anomalías y fraude.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('single')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'single'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <DocumentTextIcon className="inline-block h-5 w-5 mr-2" />
            Análisis Individual
          </button>
          <button
            onClick={() => setActiveTab('batch')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'batch'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CloudArrowUpIcon className="inline-block h-5 w-5 mr-2" />
            Análisis por Lote
          </button>
        </nav>
      </div>

      {/* Single Transaction Form */}
      {activeTab === 'single' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Datos de la Transacción</h2>
            <form onSubmit={handleSingleAnalysis} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Valor del Acto (COP)*
                </label>
                <input
                  type="number"
                  name="valor_acto"
                  value={formData.valor_acto}
                  onChange={handleInputChange}
                  required
                  className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                  placeholder="250000000"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Acto*
                  </label>
                  <select
                    name="tipo_acto"
                    value={formData.tipo_acto}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                  >
                    <option value="compraventa">Compraventa</option>
                    <option value="hipoteca">Hipoteca</option>
                    <option value="donacion">Donación</option>
                    <option value="permuta">Permuta</option>
                    <option value="otro">Otro</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fecha del Acto*
                  </label>
                  <input
                    type="date"
                    name="fecha_acto"
                    value={formData.fecha_acto}
                    onChange={handleInputChange}
                    required
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Departamento*
                  </label>
                  <input
                    type="text"
                    name="departamento"
                    value={formData.departamento}
                    onChange={handleInputChange}
                    required
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                    placeholder="CUNDINAMARCA"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Municipio*
                  </label>
                  <input
                    type="text"
                    name="municipio"
                    value={formData.municipio}
                    onChange={handleInputChange}
                    required
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                    placeholder="BOGOTA"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Predio*
                  </label>
                  <select
                    name="tipo_predio"
                    value={formData.tipo_predio}
                    onChange={handleInputChange}
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                  >
                    <option value="urbano">Urbano</option>
                    <option value="rural">Rural</option>
                    <option value="mixto">Mixto</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Número de Intervinientes*
                  </label>
                  <input
                    type="number"
                    name="numero_intervinientes"
                    value={formData.numero_intervinientes}
                    onChange={handleInputChange}
                    required
                    min="1"
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estado del Folio*
                </label>
                <select
                  name="estado_folio"
                  value={formData.estado_folio}
                  onChange={handleInputChange}
                  className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                >
                  <option value="activo">Activo</option>
                  <option value="cancelado">Cancelado</option>
                  <option value="cerrado">Cerrado</option>
                  <option value="suspendido">Suspendido</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Área Terreno (m²)
                  </label>
                  <input
                    type="number"
                    name="area_terreno"
                    value={formData.area_terreno}
                    onChange={handleInputChange}
                    step="0.01"
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                    placeholder="120.5"
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
                    onChange={handleInputChange}
                    step="0.01"
                    className="mt-1 block w-full px-4 py-2 rounded-md border border-gray-300 bg-white shadow-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:outline-none transition-colors"
                    placeholder="85.3"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? <LoadingSpinner size="sm" /> : 'Analizar Transacción'}
              </button>
            </form>
          </div>

          {/* Results */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Resultado del Análisis</h2>
            
            {error && (
              <div className="rounded-md bg-red-50 p-4 mb-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Clasificación:</span>
                  <RiskBadge level={result.result.classification} showDot />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-gray-600">Score de Anomalía:</span>
                    <span className="font-semibold">
                      {(result.result.anomaly_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        result.result.anomaly_score > 0.7
                          ? 'bg-red-600'
                          : result.result.anomaly_score > 0.4
                          ? 'bg-yellow-600'
                          : 'bg-green-600'
                      }`}
                      style={{ width: `${result.result.anomaly_score * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Explicación:</h3>
                  <p className="text-sm text-gray-600">{result.result.explanation}</p>
                </div>

                {result.result.contributing_features.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">
                      Factores Contribuyentes:
                    </h3>
                    <ul className="space-y-2">
                      {result.result.contributing_features.map((feature, idx) => (
                        <li key={idx} className="text-sm">
                          <span className="font-medium">{feature.feature_name}:</span>{' '}
                          {feature.explanation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.result.recommendations.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Recomendaciones:</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                      {result.result.recommendations.map((rec, idx) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="text-xs text-gray-500 pt-4 border-t">
                  Tiempo de procesamiento: {result.processing_time_ms.toFixed(2)} ms
                </div>
              </div>
            )}

            {!result && !error && (
              <div className="text-center text-gray-500 py-12">
                <DocumentTextIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Los resultados aparecerán aquí</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Batch Analysis */}
      {activeTab === 'batch' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Análisis por Lote</h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
            <CloudArrowUpIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <label className="cursor-pointer">
              <span className="text-primary-600 hover:text-primary-500 font-medium">
                Selecciona un archivo
              </span>
              <input
                type="file"
                accept=".csv,.parquet"
                onChange={handleBatchUpload}
                className="hidden"
                disabled={loading}
              />
            </label>
            <p className="text-sm text-gray-500 mt-2">
              CSV o Parquet hasta 100MB
            </p>
          </div>

          {loading && (
            <div className="mt-8 text-center">
              <LoadingSpinner size="lg" />
              <p className="text-gray-600 mt-4">Procesando archivo...</p>
            </div>
          )}

          {error && (
            <div className="mt-6 rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {batchResult && (
            <div className="mt-8 space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-semibold">
                    {batchResult.stats.total_transactions.toLocaleString()}
                  </p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-green-600">Normal</p>
                  <p className="text-2xl font-semibold text-green-700">
                    {batchResult.stats.normal_count.toLocaleString()}
                  </p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <p className="text-sm text-yellow-600">Sospechoso</p>
                  <p className="text-2xl font-semibold text-yellow-700">
                    {batchResult.stats.suspicious_count.toLocaleString()}
                  </p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-sm text-red-600">Alto Riesgo</p>
                  <p className="text-2xl font-semibold text-red-700">
                    {batchResult.stats.high_risk_count.toLocaleString()}
                  </p>
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-2">
                  Transacciones de Alto Riesgo (Top 10)
                </h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Índice
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Score
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Clasificación
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {batchResult.high_risk_transactions.slice(0, 10).map((tx) => (
                        <tr key={tx.row_index}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {tx.row_index}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {(tx.analysis.anomaly_score * 100).toFixed(1)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <RiskBadge level={tx.analysis.classification} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
