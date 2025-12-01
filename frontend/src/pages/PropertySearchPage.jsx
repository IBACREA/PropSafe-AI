import { useState } from 'react';
import { MagnifyingGlassIcon, ExclamationTriangleIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/LoadingSpinner';
import api from '../services/api';

export default function PropertySearchPage() {
  const [matricula, setMatricula] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!matricula.trim()) {
      setError('Por favor ingresa un número de matrícula');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.searchProperty(matricula.trim());
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al buscar la propiedad');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (!score) return 'gray';
    if (score < 0.4) return 'green';
    if (score < 0.7) return 'yellow';
    return 'red';
  };

  const getRiskLabel = (score) => {
    if (!score) return 'Sin determinar';
    if (score < 0.4) return 'Riesgo Bajo';
    if (score < 0.7) return 'Riesgo Medio';
    return 'Riesgo Alto';
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      // dateStr viene como "YYYY-MM-DD"
      const [year, month, day] = dateStr.split('-');
      return `${day}/${month}/${year}`;
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header con disclaimer */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Búsqueda de Propiedades
          </h1>
          <p className="text-gray-600 mb-4">
            Consulta el historial de transacciones y análisis de riesgo de cualquier propiedad
          </p>
          
          {/* Disclaimer destacado */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
            <div className="flex">
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400 mr-3 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-medium text-yellow-800">
                  Aviso Legal Importante
                </h3>
                <p className="text-sm text-yellow-700 mt-1">
                  Esta información es <strong>probabilística y con fines informativos únicamente</strong>. 
                  No constituye asesoría legal, notarial o financiera. Los datos pueden contener errores 
                  o estar desactualizados. Siempre consulte fuentes oficiales (Superintendencia de Notariado 
                  y Registro) antes de tomar decisiones sobre propiedades.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Formulario de búsqueda */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <label htmlFor="matricula" className="block text-sm font-medium text-gray-700 mb-2">
                Número de Matrícula Inmobiliaria
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  id="matricula"
                  value={matricula}
                  onChange={(e) => setMatricula(e.target.value)}
                  placeholder="Ej: 050-123456, 110-789012"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2 transition-colors"
                >
                  {loading ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Buscando...
                    </>
                  ) : (
                    <>
                      <MagnifyingGlassIcon className="h-5 w-5" />
                      Buscar
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Ingresa el número de matrícula inmobiliaria completo (incluye dígito de verificación si aplica)
              </p>
            </div>
          </form>

          {error && (
            <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4 rounded">
              <div className="flex">
                <XCircleIcon className="h-5 w-5 text-red-400 mr-2" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Resultados */}
        {result && (
          <div className="space-y-6">
            {/* No encontrada */}
            {!result.encontrada && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-center py-8">
                  <XCircleIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Propiedad no encontrada
                  </h3>
                  <p className="text-gray-600">
                    No se encontraron registros para la matrícula <strong>{result.matricula}</strong> en la base de datos.
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Verifica que el número esté correcto o intenta con otra matrícula.
                  </p>
                </div>
              </div>
            )}

            {/* Encontrada - Resumen */}
            {result.encontrada && (
              <>
                {/* Card de resumen */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900 mb-1">
                        Matrícula: {result.matricula}
                      </h2>
                      {result.ubicacion && (
                        <p className="text-gray-600">
                          {result.ubicacion.municipio}, {result.ubicacion.departamento}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <span className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${
                        getRiskColor(result.score_riesgo) === 'green' ? 'bg-green-100 text-green-800' :
                        getRiskColor(result.score_riesgo) === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {getRiskLabel(result.score_riesgo)}
                      </span>
                      {result.score_riesgo !== null && (
                        <p className="text-sm text-gray-500 mt-1">
                          Score: {(result.score_riesgo * 100).toFixed(1)}%
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Métricas principales */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-blue-600 font-medium mb-1">Total Transacciones</p>
                      <p className="text-2xl font-bold text-blue-900">{result.total_transacciones}</p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-sm text-green-600 font-medium mb-1">Precio Promedio</p>
                      <p className="text-xl font-bold text-green-900">
                        {formatCurrency(result.precio_promedio)}
                      </p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <p className="text-sm text-purple-600 font-medium mb-1">Última Transacción</p>
                      <p className="text-xl font-bold text-purple-900">
                        {formatCurrency(result.precio_ultima)}
                      </p>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <p className="text-sm text-orange-600 font-medium mb-1">Tasa Anomalías</p>
                      <p className="text-2xl font-bold text-orange-900">
                        {result.tasa_anomalias?.toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {/* Alertas */}
                  {result.alertas && result.alertas.length > 0 && (
                    <div className="space-y-2">
                      {result.alertas.map((alerta, index) => (
                        <div
                          key={index}
                          className={`flex items-start gap-3 p-3 rounded-lg ${
                            alerta.includes('🚨') ? 'bg-red-50 border border-red-200' :
                            alerta.includes('⚠️') ? 'bg-yellow-50 border border-yellow-200' :
                            'bg-green-50 border border-green-200'
                          }`}
                        >
                          <span className="text-lg">{alerta.substring(0, 2)}</span>
                          <p className="text-sm text-gray-700 flex-1">{alerta.substring(2).trim()}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Historial de transacciones */}
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-bold text-gray-900 mb-4">
                    Historial de Transacciones ({result.historial.length})
                  </h3>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Fecha
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Tipo Acto
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Valor
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Ubicación
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Tipo Predio
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Interv.
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Estado
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {result.historial.map((tx, index) => (
                          <tr key={index} className={tx.es_anomalo ? 'bg-red-50' : ''}>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {formatDate(tx.fecha)}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {tx.tipo_acto}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                              {formatCurrency(tx.valor)}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {tx.municipio}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {tx.tipo_predio}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 text-center">
                              {tx.count_intervinientes}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              {tx.es_anomalo ? (
                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                  <ExclamationTriangleIcon className="h-3 w-3" />
                                  Anómala
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  <CheckCircleIcon className="h-3 w-3" />
                                  Normal
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Info adicional */}
                <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-lg">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">
                    Interpretación de resultados
                  </h4>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• <strong>Riesgo Bajo:</strong> Historial consistente, sin señales de alerta significativas</li>
                    <li>• <strong>Riesgo Medio:</strong> Algunas anomalías detectadas, se recomienda verificación adicional</li>
                    <li>• <strong>Riesgo Alto:</strong> Múltiples señales de alerta, revisar detalladamente antes de cualquier decisión</li>
                    <li>• Las transacciones marcadas como "Anómala" presentan patrones inusuales según nuestros modelos ML</li>
                  </ul>
                </div>
              </>
            )}
          </div>
        )}

        {/* Ejemplos de búsqueda (solo si no hay resultados) */}
        {!result && !loading && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">
              ¿Cómo buscar una propiedad?
            </h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>
                La matrícula inmobiliaria es el número único que identifica cada propiedad en Colombia. 
                Lo encuentras en:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>Certificado de tradición y libertad</li>
                <li>Escritura pública de compraventa</li>
                <li>Recibo de impuesto predial</li>
              </ul>
              <p className="font-medium mt-4">
                Formato típico: XXX-YYYYYY (donde XXX es el código de oficina de registro)
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
