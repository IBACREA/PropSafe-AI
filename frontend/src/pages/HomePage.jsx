import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  MapIcon, 
  ChartBarIcon, 
  ChatBubbleLeftRightIcon,
  ShieldCheckIcon,
  DocumentMagnifyingGlassIcon,
  CloudArrowUpIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline'

const features = [
  {
    name: 'Mapa Interactivo',
    description: 'Visualiza transacciones y anomalías en un mapa geográfico de Colombia.',
    icon: MapIcon,
    href: '/map',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  {
    name: 'Analizador de Transacciones',
    description: 'Analiza transacciones individuales o en lote para detectar anomalías y riesgos.',
    icon: ChartBarIcon,
    href: '/analyzer',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  {
    name: 'Asistente Inteligente',
    description: 'Consulta información sobre transacciones usando lenguaje natural.',
    icon: ChatBubbleLeftRightIcon,
    href: '/chat',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
]

export default function HomePage() {
  const navigate = useNavigate()
  const [quickAnalysis, setQuickAnalysis] = useState({
    valor: '',
    municipio: 'BOGOTA',
  })

  const handleQuickAnalysis = (e) => {
    e.preventDefault()
    // Navegar al analizador con los datos
    navigate('/analyzer', { 
      state: { 
        valor_acto: parseFloat(quickAnalysis.valor),
        municipio: quickAnalysis.municipio 
      } 
    })
  }

  return (
    <div className="bg-white">
      {/* Hero section */}
      <div className="relative isolate overflow-hidden bg-gradient-to-b from-primary-100/20">
        <div className="mx-auto max-w-7xl px-6 pb-24 pt-10 sm:pb-32 lg:flex lg:px-8 lg:py-40">
          <div className="mx-auto max-w-2xl lg:mx-0 lg:max-w-xl lg:flex-shrink-0 lg:pt-8">
            <div className="flex items-center gap-3 mb-6">
              <ShieldCheckIcon className="h-12 w-12 text-primary-600" />
              <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
                Análisis de Riesgo Inmobiliario
              </h1>
            </div>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Plataforma avanzada de Machine Learning para identificar anomalías en 
              transacciones inmobiliarias de Colombia. Detecta patrones inusuales y 
              evalúa riesgos en tiempo real.
            </p>

            {/* Quick Analysis Form */}
            <form onSubmit={handleQuickAnalysis} className="mt-10 p-6 bg-white rounded-lg shadow-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Análisis Rápido</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="valor" className="block text-sm font-medium text-gray-700 mb-1">
                    Valor de la transacción (COP)
                  </label>
                  <input
                    type="number"
                    id="valor"
                    value={quickAnalysis.valor}
                    onChange={(e) => setQuickAnalysis({...quickAnalysis, valor: e.target.value})}
                    placeholder="Ej: 250000000"
                    className="w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="municipio" className="block text-sm font-medium text-gray-700 mb-1">
                    Municipio
                  </label>
                  <select
                    id="municipio"
                    value={quickAnalysis.municipio}
                    onChange={(e) => setQuickAnalysis({...quickAnalysis, municipio: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 bg-white rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="BOGOTA">Bogotá</option>
                    <option value="MEDELLIN">Medellín</option>
                    <option value="CALI">Cali</option>
                    <option value="BARRANQUILLA">Barranquilla</option>
                    <option value="CARTAGENA">Cartagena</option>
                  </select>
                </div>
                <button
                  type="submit"
                  className="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors flex items-center justify-center gap-2"
                >
                  Analizar Ahora
                  <ArrowRightIcon className="h-4 w-4" />
                </button>
              </div>
            </form>

            <div className="mt-6 flex items-center gap-x-6">
              <Link
                to="/dashboard"
                className="rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700"
              >
                Ver Dashboard
              </Link>
              <Link
                to="/map"
                className="text-sm font-semibold leading-6 text-gray-900 hover:text-primary-600"
              >
                Mapa Interactivo <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
          <div className="mx-auto mt-16 flex max-w-2xl sm:mt-24 lg:ml-10 lg:mr-0 lg:mt-0 lg:max-w-none lg:flex-none xl:ml-32">
            <div className="max-w-3xl flex-none sm:max-w-5xl lg:max-w-none">
              <div className="-m-2 rounded-xl bg-gray-900/5 p-2 ring-1 ring-inset ring-gray-900/10 lg:-m-4 lg:rounded-2xl lg:p-4">
                <DocumentMagnifyingGlassIcon className="h-64 w-64 text-primary-600 opacity-50" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features section */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-24 sm:py-32">
        <div className="mx-auto max-w-2xl lg:text-center">
          <h2 className="text-base font-semibold leading-7 text-primary-600">
            Herramientas disponibles
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Funcionalidades de la plataforma
          </p>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Analiza transacciones inmobiliarias con tecnología de Machine Learning 
            y detecta patrones de riesgo en tiempo real.
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {features.map((feature) => (
              <Link
                key={feature.name}
                to={feature.href}
                className="flex flex-col group hover:bg-gray-50 p-6 rounded-lg transition-colors"
              >
                <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${feature.bgColor}`}>
                    <feature.icon className={`h-6 w-6 ${feature.color}`} aria-hidden="true" />
                  </div>
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                  <p className="flex-auto">{feature.description}</p>
                  <p className="mt-6">
                    <span className={`text-sm font-semibold ${feature.color} group-hover:underline`}>
                      Explorar →
                    </span>
                  </p>
                </dd>
              </Link>
            ))}
          </dl>
        </div>
      </div>

      {/* CTA section */}
      <div className="bg-primary-600">
        <div className="px-6 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Comienza a analizar transacciones
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-primary-100">
              Carga datos de transacciones y obtén análisis de riesgo instantáneo con Machine Learning.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                to="/analyzer"
                className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-primary-600 shadow-sm hover:bg-primary-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                <CloudArrowUpIcon className="inline-block h-5 w-5 mr-2" />
                Ir al Analizador
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
