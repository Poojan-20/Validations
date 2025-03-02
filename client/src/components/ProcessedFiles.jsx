import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { FiDownload, FiFile, FiRefreshCw } from 'react-icons/fi'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card'
import { Button } from './ui/button'
import SummaryStats from './SummaryStats'

const ProcessedFiles = () => {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [statsLoading, setStatsLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [summaryStats, setSummaryStats] = useState(null)
  const [error, setError] = useState(null)

  const fetchFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get('/get_processed_files')
      console.log('Fetched files:', response.data)
      
      if (Array.isArray(response.data)) {
        setFiles(response.data)
      } else {
        console.error('Expected array of files but got:', response.data)
        setError('Invalid response format from server')
      }
      
      // Reset selected file and stats when refreshing the file list
      setSelectedFile(null)
      setSummaryStats(null)
    } catch (error) {
      console.error('Error fetching files:', error)
      setError('Failed to fetch files')
    } finally {
      setLoading(false)
    }
  }

  const fetchSummaryStats = async (filename) => {
    if (!filename) {
      console.error('No filename provided to fetchSummaryStats')
      return
    }
    
    console.log('Fetching summary stats for:', filename)
    setStatsLoading(true)
    setError(null)
    
    try {
      const url = `/get_summary_stats/${encodeURIComponent(filename)}`
      console.log('Making API call to:', url)
      
      const response = await axios.get(url)
      console.log('Received summary stats:', response.data)
      
      if (response.data && typeof response.data === 'object') {
        if (response.data.error) {
          throw new Error(response.data.error)
        }
        setSummaryStats(response.data)
      } else {
        console.error('Expected object but got:', response.data)
        throw new Error('Invalid response format from server')
      }
    } catch (error) {
      console.error('Error fetching summary stats:', error)
      setError(`Failed to fetch summary statistics: ${error.message}`)
      setSummaryStats(null)
    } finally {
      setStatsLoading(false)
    }
  }

  useEffect(() => {
    console.log('Component mounted, fetching files...')
    fetchFiles()
  }, [])

  const handleFileSelect = async (file) => {
    console.log('Selected file:', file)
    setSelectedFile(file)
    setSummaryStats(null) // Clear previous stats
    await fetchSummaryStats(file.name)
  }

  const handleDownload = (filename) => {
    window.location.href = `/download_processed/${filename}`
  }

  return (
    <div className="space-y-8">
      {/* Processed Files List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xl">Processed Files</CardTitle>
          <Button 
            onClick={fetchFiles} 
            variant="ghost" 
            size="icon"
            title="Refresh"
            disabled={loading}
          >
            <FiRefreshCw className={loading ? 'animate-spin' : ''} />
          </Button>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="text-red-500 mb-4 p-2 bg-red-50 rounded">
              {error}
            </div>
          )}
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              <FiRefreshCw className="mx-auto text-4xl mb-2 animate-spin" />
              <p>Loading files...</p>
            </div>
          ) : files.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <FiFile className="mx-auto text-4xl mb-2" />
              <p>No processed files yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {files.map((file, index) => (
                <div 
                  key={index} 
                  className={`border rounded-lg p-4 cursor-pointer hover:bg-accent/50 transition-colors ${
                    selectedFile?.name === file.name ? 'bg-accent border-primary' : ''
                  }`}
                  onClick={() => handleFileSelect(file)}
                >
                  <div className="flex justify-between items-start">
                    <div className="overflow-hidden">
                      <p className="font-medium truncate text-foreground" title={file.name}>
                        {file.name}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        {file.date} • {file.size}
                      </p>
                    </div>
                    <Button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDownload(file.name)
                      }}
                      variant="ghost"
                      size="icon"
                      title="Download"
                      className="ml-2 flex-shrink-0"
                    >
                      <FiDownload className="text-primary" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Summary Stats Section */}
      {selectedFile && (
        <Card>
          <CardHeader className="border-b">
            <CardTitle>Analysis Results</CardTitle>
            <CardDescription>
              Showing statistics for {selectedFile.name}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {statsLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                <div className="flex items-center justify-center">
                  <FiRefreshCw className="animate-spin mr-2" />
                  Loading statistics...
                </div>
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-500">
                {error}
              </div>
            ) : summaryStats ? (
              <SummaryStats summaryData={summaryStats} />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No statistics available
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ProcessedFiles 