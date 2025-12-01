import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import MapPage from './pages/MapPage'
import AnalyzerPage from './pages/AnalyzerPage'
import PropertySearchPage from './pages/PropertySearchPage'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="map" element={<MapPage />} />
        <Route path="analyzer" element={<AnalyzerPage />} />
        <Route path="property-search" element={<PropertySearchPage />} />
      </Route>
    </Routes>
  )
}

export default App
