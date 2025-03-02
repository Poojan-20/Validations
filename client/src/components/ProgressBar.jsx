import React, { useEffect, useState } from 'react'
import { Progress } from './ui/progress'

const ProgressBar = ({ progress }) => {
  const [eventSource, setEventSource] = useState(null)
  const [currentProgress, setCurrentProgress] = useState(progress)

  useEffect(() => {
    // Connect to the server-sent events endpoint directly
    const source = new EventSource('/progress')
    
    source.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setCurrentProgress(data)
      
      if (data.complete) {
        source.close()
      }
    }
    
    setEventSource(source)
    
    return () => {
      if (source) {
        source.close()
      }
    }
  }, [])

  const getStepLabel = (step) => {
    switch (step) {
      case 'loading':
        return 'Loading files...'
      case 'validation':
        return 'Validating data...'
      case 'report':
        return 'Generating report...'
      default:
        return 'Processing...'
    }
  }

  return (
    <div className="mb-6">
      <div className="flex justify-between mb-2">
        <span className="text-sm font-medium text-foreground">{getStepLabel(currentProgress.step)}</span>
        <span className="text-sm font-medium text-foreground">{currentProgress.percentage}%</span>
      </div>
      <Progress value={currentProgress.percentage} className="h-2" />
    </div>
  )
}

export default ProgressBar 