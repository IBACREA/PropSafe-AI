import React, { useState, useEffect, useMemo } from 'react'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix para los iconos de Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Datos de prueba para el mapa de Colombia
const COLOMBIA_CITIES = [
  { name: 'BOGOTA', lat: 4.7110, lng: -74.0721, count: 15000, anomaly_rate: 0.15 },
  { name: 'MEDELLIN', lat: 6.2476, lng: -75.5658, count: 8000, anomaly_rate: 0.12 },
  { name: 'CALI', lat: 3.4516, lng: -76.5320, count: 6500, anomaly_rate: 0.18 },
  { name: 'BARRANQUILLA', lat: 10.9639, lng: -74.7964, count: 4200, anomaly_rate: 0.10 },
  { name: 'CARTAGENA', lat: 10.3910, lng: -75.4794, count: 3800, anomaly_rate: 0.22 },
  { name: 'CUCUTA', lat: 7.8939, lng: -72.5078, count: 2100, anomaly_rate: 0.14 },
  { name: 'BUCARAMANGA', lat: 7.1254, lng: -73.1198, count: 2800, anomaly_rate: 0.11 },
  { name: 'PEREIRA', lat: 4.8133, lng: -75.6961, count: 1900, anomaly_rate: 0.16 },
  { name: 'MANIZALES', lat: 5.0703, lng: -75.5138, count: 1500, anomaly_rate: 0.13 },
  { name: 'IBAGUE', lat: 4.4389, lng: -75.2322, count: 1400, anomaly_rate: 0.17 },
]

const getRiskColor = (rate) => {
  if (rate > 0.2) return '#ef4444'
  if (rate > 0.15) return '#f59e0b'
  return '#10b981'
}

const getRiskLabel = (rate) => {
  if (rate > 0.2) return 'Alto riesgo'
  if (rate > 0.15) return 'Riesgo medio'
  return 'Bajo riesgo'
}

const getCircleRadius = (count) => {
  if (count > 10000) return 25
  if (count > 5000) return 18
  if (count > 2000) return 12
  return 8
}

export default function MapPage() {
  const [cities] = useState(COLOMBIA_CITIES)
  const [mapInstance, setMapInstance] = useState(null)

  useEffect(() => {
    // Verificar si el contenedor ya tiene un mapa inicializado
    const container = document.getElementById('map-container')
    if (!container || container._leaflet_id) {
      return
    }

    if (!mapInstance) {
      // Crear el mapa cuando el componente se monte
      const map = L.map('map-container').setView([4.5709, -74.2973], 6)
      
      // Agregar capa de tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map)
      
      // Agregar círculos para cada ciudad
      cities.forEach(city => {
        const circle = L.circleMarker([city.lat, city.lng], {
          radius: getCircleRadius(city.count) / 2,
          fillColor: getRiskColor(city.anomaly_rate),
          fillOpacity: 0.7,
          color: 'white',
          weight: 2
        }).addTo(map)
        
        // Agregar popup
        circle.bindPopup(`
          <div style="padding: 8px;">
            <h3 style="font-weight: bold; font-size: 1.125rem; margin-bottom: 8px;">${city.name}</h3>
            <div style="font-size: 0.875rem;">
              <p><strong>Transacciones:</strong> ${city.count.toLocaleString()}</p>
              <p><strong>Tasa anomalías:</strong> ${(city.anomaly_rate * 100).toFixed(1)}%</p>
              <p><strong>Clasificación:</strong> ${getRiskLabel(city.anomaly_rate)}</p>
            </div>
          </div>
        `)
      })
      
      setMapInstance(map)
    }
    
    return () => {
      if (mapInstance) {
        mapInstance.remove()
      }
    }
  }, [])

  return (
    <div className="h-screen relative">
      {/* Panel de información */}
      <div className="absolute top-4 left-4 z-[1000] bg-white p-6 rounded-lg shadow-xl max-w-sm">
        <h2 className="text-xl font-bold mb-2 text-gray-900">Mapa de Transacciones</h2>
        <p className="text-sm text-gray-600 mb-4">
          Colombia - Análisis de riesgo por ciudad
        </p>
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full bg-green-500" />
            <span>Bajo riesgo (&lt;15%)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full bg-yellow-500" />
            <span>Riesgo medio (15-20%)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full bg-red-500" />
            <span>Alto riesgo (&gt;20%)</span>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t">
          <p className="text-xs text-gray-500">
            {cities.length} ciudades • {cities.reduce((sum, c) => sum + c.count, 0).toLocaleString()} transacciones
          </p>
        </div>
      </div>

      {/* Contenedor del mapa */}
      <div id="map-container" style={{ height: '100%', width: '100%' }} />
    </div>
  )
}
