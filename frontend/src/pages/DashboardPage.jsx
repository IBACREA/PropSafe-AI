import React, { useState, useEffect } from 'react'
import {
  ChartBarIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  DocumentCheckIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline'
import PriceValidator from '../components/PriceValidator'

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState('30d')
  const [loading, setLoading] = useState(false)

  // Datos simulados - en producción vendrían del backend
  const kpis = {
    totalTransacciones: 34127580,
    transaccionesMes: 145230,
    tasaAnomalias: 12.4,
    valorPromedio: 285000000,
    alertasFraude: 1847,
    municipiosMonitoreados: 1105,
    calidadDatos: 94.2,
    tiempoProcesamientoPromedio: 2.3,
  }

  const tendencias = {
    transacciones: { valor: 8.5, tipo: 'up' },
    anomalias: { valor: -3.2, tipo: 'down' },
    fraude: { valor: 12.1, tipo: 'up' },
    calidad: { valor: 2.1, tipo: 'up' },
  }

  const alertasCriticas = [
    {
      id: 1,
      tipo: 'fraude',
      severidad: 'alta',
      municipio: 'BOGOTA',
      descripcion: 'Patrón de 15 transacciones con valores sospechosamente bajos',
      fecha: '2025-11-27 14:32',
      valorPromedio: 45000000,
    },
    {
      id: 2,
      tipo: 'anomalia',
      severidad: 'media',
      municipio: 'MEDELLIN',
      descripcion: 'Aumento del 40% en transacciones respecto al promedio mensual',
      fecha: '2025-11-27 13:15',
      valorPromedio: 320000000,
    },
    {
      id: 3,
      tipo: 'calidad',
      severidad: 'media',
      municipio: 'CALI',
      descripcion: '23 registros con campos obligatorios incompletos',
      fecha: '2025-11-27 11:45',
      valorPromedio: null,
    },
    {
      id: 4,
      tipo: 'fraude',
      severidad: 'alta',
      municipio: 'CARTAGENA',
      descripcion: 'Duplicación de matrícula inmobiliaria en 8 transacciones',
      fecha: '2025-11-27 10:20',
      valorPromedio: 180000000,
    },
  ]

  const distribucionAnomalias = [
    { tipo: 'Valores atípicos', cantidad: 8542, porcentaje: 48.2 },
    { tipo: 'Duplicidad sospechosa', cantidad: 3211, porcentaje: 18.1 },
    { tipo: 'Errores de anotación', cantidad: 2890, porcentaje: 16.3 },
    { tipo: 'Inconsistencia temporal', cantidad: 1847, porcentaje: 10.4 },
    { tipo: 'Datos incompletos', cantidad: 1234, porcentaje: 7.0 },
  ]

  const municipiosCriticos = [
    { nombre: 'BOGOTA', alertas: 342, tasa: 15.2, tendencia: 'up' },
    { nombre: 'MEDELLIN', alertas: 189, tasa: 13.8, tendencia: 'up' },
    { nombre: 'CALI', alertas: 156, tasa: 14.1, tendencia: 'down' },
    { nombre: 'BARRANQUILLA', alertas: 98, tasa: 11.3, tendencia: 'up' },
    { nombre: 'CARTAGENA', alertas: 87, tasa: 18.7, tendencia: 'up' },
  ]

  const getSeveridadColor = (severidad) => {
    switch (severidad) {
      case 'alta':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'media':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'baja':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getTipoIcon = (tipo) => {
    switch (tipo) {
      case 'fraude':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
      case 'anomalia':
        return <ChartBarIcon className="h-5 w-5 text-yellow-600" />
      case 'calidad':
        return <DocumentCheckIcon className="h-5 w-5 text-blue-600" />
      default:
        return <ShieldCheckIcon className="h-5 w-5 text-gray-600" />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Dashboard de Monitoreo
          </h1>
          <p className="mt-2 text-gray-600">
            Indicadores clave de riesgo, calidad y detección de fraude en tiempo real
          </p>
        </div>

        {/* Filtro de tiempo */}
        <div className="mb-6 flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Período:</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="24h">Últimas 24 horas</option>
            <option value="7d">Últimos 7 días</option>
            <option value="30d">Últimos 30 días</option>
            <option value="90d">Últimos 90 días</option>
            <option value="1y">Último año</option>
          </select>
        </div>

        {/* KPIs principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Transacciones */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Transacciones</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {kpis.totalTransacciones.toLocaleString()}
                </p>
                <div className="flex items-center mt-2 text-sm">
                  <ArrowTrendingUpIcon className="h-4 w-4 text-green-600 mr-1" />
                  <span className="text-green-600 font-medium">+{tendencias.transacciones.valor}%</span>
                  <span className="text-gray-500 ml-1">vs mes anterior</span>
                </div>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <ChartBarIcon className="h-8 w-8 text-blue-600" />
              </div>
            </div>
          </div>

          {/* Tasa de Anomalías */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tasa de Anomalías</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {kpis.tasaAnomalias}%
                </p>
                <div className="flex items-center mt-2 text-sm">
                  <ArrowTrendingDownIcon className="h-4 w-4 text-green-600 mr-1" />
                  <span className="text-green-600 font-medium">{tendencias.anomalias.valor}%</span>
                  <span className="text-gray-500 ml-1">vs mes anterior</span>
                </div>
              </div>
              <div className="p-3 bg-yellow-100 rounded-lg">
                <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600" />
              </div>
            </div>
          </div>

          {/* Alertas de Fraude */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Alertas de Fraude</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {kpis.alertasFraude.toLocaleString()}
                </p>
                <div className="flex items-center mt-2 text-sm">
                  <ArrowTrendingUpIcon className="h-4 w-4 text-red-600 mr-1" />
                  <span className="text-red-600 font-medium">+{tendencias.fraude.valor}%</span>
                  <span className="text-gray-500 ml-1">vs mes anterior</span>
                </div>
              </div>
              <div className="p-3 bg-red-100 rounded-lg">
                <ShieldCheckIcon className="h-8 w-8 text-red-600" />
              </div>
            </div>
          </div>

          {/* Calidad de Datos */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Calidad de Datos</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {kpis.calidadDatos}%
                </p>
                <div className="flex items-center mt-2 text-sm">
                  <ArrowTrendingUpIcon className="h-4 w-4 text-green-600 mr-1" />
                  <span className="text-green-600 font-medium">+{tendencias.calidad.valor}%</span>
                  <span className="text-gray-500 ml-1">vs mes anterior</span>
                </div>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <DocumentCheckIcon className="h-8 w-8 text-green-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Grid de 2 columnas */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Alertas Críticas */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Alertas Críticas Recientes
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {alertasCriticas.map((alerta) => (
                  <div
                    key={alerta.id}
                    className={`p-4 rounded-lg border ${getSeveridadColor(alerta.severidad)}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-1">{getTipoIcon(alerta.tipo)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="font-semibold text-sm">{alerta.municipio}</h3>
                          <span className="text-xs font-medium px-2 py-1 rounded-full bg-white">
                            {alerta.severidad.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">{alerta.descripcion}</p>
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <span className="flex items-center">
                            <ClockIcon className="h-3 w-3 mr-1" />
                            {alerta.fecha}
                          </span>
                          {alerta.valorPromedio && (
                            <span className="flex items-center">
                              <CurrencyDollarIcon className="h-3 w-3 mr-1" />
                              ${(alerta.valorPromedio / 1000000).toFixed(1)}M
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Distribución de Anomalías */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Distribución de Anomalías por Tipo
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {distribucionAnomalias.map((item, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">{item.tipo}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-900">
                          {item.cantidad.toLocaleString()}
                        </span>
                        <span className="text-xs text-gray-500">({item.porcentaje}%)</span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all"
                        style={{ width: `${item.porcentaje}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-gray-700">Total</span>
                  <span className="text-lg font-bold text-gray-900">
                    {distribucionAnomalias
                      .reduce((sum, item) => sum + item.cantidad, 0)
                      .toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Municipios Críticos */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Top 5 Municipios con Mayor Riesgo
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Municipio
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Alertas Activas
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tasa de Anomalías
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tendencia
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acción
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {municipiosCriticos.map((municipio, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <MapPinIcon className="h-5 w-5 text-gray-400 mr-2" />
                        <span className="text-sm font-medium text-gray-900">
                          {municipio.nombre}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">{municipio.alertas}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-red-600">
                        {municipio.tasa}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {municipio.tendencia === 'up' ? (
                        <span className="flex items-center text-sm text-red-600">
                          <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />
                          Aumentando
                        </span>
                      ) : (
                        <span className="flex items-center text-sm text-green-600">
                          <ArrowTrendingDownIcon className="h-4 w-4 mr-1" />
                          Disminuyendo
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button className="text-sm text-primary-600 hover:text-primary-800 font-medium">
                        Ver detalles →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Métricas adicionales */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Municipios Monitoreados</h3>
              <MapPinIcon className="h-5 w-5 text-gray-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{kpis.municipiosMonitoreados}</p>
            <p className="text-xs text-gray-500 mt-1">De 1,105 municipios en Colombia</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Valor Promedio</h3>
              <CurrencyDollarIcon className="h-5 w-5 text-gray-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              ${(kpis.valorPromedio / 1000000).toFixed(0)}M
            </p>
            <p className="text-xs text-gray-500 mt-1">COP por transacción</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Tiempo de Procesamiento</h3>
              <ClockIcon className="h-5 w-5 text-gray-400" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {kpis.tiempoProcesamientoPromedio}s
            </p>
            <p className="text-xs text-gray-500 mt-1">Promedio por análisis</p>
          </div>
        </div>

        {/* Validador de Precios con IA */}
        <PriceValidator />
      </div>
    </div>
  )
}
