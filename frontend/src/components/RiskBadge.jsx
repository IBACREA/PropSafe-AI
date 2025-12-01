import React from 'react'
import clsx from 'clsx'

const riskLevelConfig = {
  normal: {
    label: 'Normal',
    className: 'bg-green-100 text-green-800',
    dotColor: 'bg-green-400',
  },
  suspicious: {
    label: 'Sospechoso',
    className: 'bg-yellow-100 text-yellow-800',
    dotColor: 'bg-yellow-400',
  },
  'high-risk': {
    label: 'Alto Riesgo',
    className: 'bg-red-100 text-red-800',
    dotColor: 'bg-red-400',
  },
}

export default function RiskBadge({ level, showDot = false, className = '' }) {
  const config = riskLevelConfig[level] || riskLevelConfig.normal

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.className,
        className
      )}
    >
      {showDot && (
        <span className={clsx('w-2 h-2 rounded-full mr-1.5', config.dotColor)} />
      )}
      {config.label}
    </span>
  )
}
