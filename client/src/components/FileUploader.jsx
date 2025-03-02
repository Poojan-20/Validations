import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { FiUpload, FiFile, FiX } from 'react-icons/fi'
import { Button } from './ui/button'
import { cn } from '../lib/utils'

const FileUploader = ({ setIsUploading, setProgress }) => {
  const [file1, setFile1] = useState(null)
  const [file2, setFile2] = useState(null)
  const [headers1, setHeaders1] = useState([])
  const [headers2, setHeaders2] = useState([])
  const [mapping1, setMapping1] = useState({})
  const [mapping2, setMapping2] = useState({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const requiredColumns = ['txn_id', 'revenue', 'sale_amount', 'status', 'brand', 'created']

  const onDrop1 = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) {
      setFile1(acceptedFiles[0])
      fetchHeaders(acceptedFiles[0], setHeaders1, setMapping1)
    }
  }, [])

  const onDrop2 = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) {
      setFile2(acceptedFiles[0])
      fetchHeaders(acceptedFiles[0], setHeaders2, setMapping2)
    }
  }, [])

  const { getRootProps: getRootProps1, getInputProps: getInputProps1 } = useDropzone({
    onDrop: onDrop1,
    accept: {
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxFiles: 1
  })

  const { getRootProps: getRootProps2, getInputProps: getInputProps2 } = useDropzone({
    onDrop: onDrop2,
    accept: {
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxFiles: 1
  })

  const fetchHeaders = async (file, setHeaders, setMapping) => {
    setLoading(true)
    setError('')
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      // Direct API call to Flask endpoint
      const response = await axios.post('/get_headers', formData)
      setHeaders(response.data.headers)
      setMapping(response.data.suggested_mapping)
    } catch (error) {
      console.error('Error fetching headers:', error)
      setError(error.response?.data?.error || 'Failed to read file headers')
    } finally {
      setLoading(false)
    }
  }

  const handleMappingChange = (column, value, setMappingFunc) => {
    setMappingFunc(prev => ({
      ...prev,
      [column]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file1 || !file2) {
      setError('Please select both files')
      return
    }
    
    // Check if all required columns are mapped
    const missingColumns1 = requiredColumns.filter(col => !mapping1[col])
    const missingColumns2 = requiredColumns.filter(col => !mapping2[col])
    
    if (missingColumns1.length > 0 || missingColumns2.length > 0) {
      setError(`Please map all required columns: ${[...missingColumns1, ...missingColumns2].join(', ')}`)
      return
    }
    
    setIsUploading(true)
    setError('')
    
    const formData = new FormData()
    formData.append('file1', file1)
    formData.append('file2', file2)
    formData.append('mapping1', JSON.stringify(mapping1))
    formData.append('mapping2', JSON.stringify(mapping2))
    
    try {
      // Direct API call to Flask endpoint
      const response = await axios.post('/upload', formData, {
        responseType: 'blob'
      })
      
      // Create a download link for the returned file
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Extract filename from Content-Disposition header if available
      const contentDisposition = response.headers['content-disposition']
      let filename = 'validation-results.xlsx'
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]*)"?/)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1]
        }
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      
      // Reset form
      setFile1(null)
      setFile2(null)
      setHeaders1([])
      setHeaders2([])
      setMapping1({})
      setMapping2({})
      
    } catch (error) {
      console.error('Error uploading files:', error)
      setError(error.response?.data?.error || 'Failed to process files')
    } finally {
      setIsUploading(false)
      setProgress({
        step: 'loading',
        percentage: 0,
        stats: {},
        complete: false
      })
    }
  }

  const removeFile = (setFileFunc, setHeadersFunc, setMappingFunc) => {
    setFileFunc(null)
    setHeadersFunc([])
    setMappingFunc({})
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && (
        <div className="mb-4 p-3 bg-destructive/10 text-destructive rounded-md border border-destructive/20">
          {error}
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <label className="block text-sm font-medium mb-2 text-foreground">File 1</label>
          {!file1 ? (
            <div 
              {...getRootProps1()} 
              className={cn(
                "border-2 border-dashed border-input rounded-md p-6 text-center hover:border-primary cursor-pointer transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              )}
            >
              <input {...getInputProps1()} />
              <FiUpload className="mx-auto text-3xl mb-2 text-muted-foreground" />
              <p className="text-muted-foreground">Drag & drop an Excel file here, or click to select</p>
            </div>
          ) : (
            <div className="border rounded-md p-4 bg-muted">
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <FiFile className="text-primary mr-2" />
                  <span className="truncate">{file1.name}</span>
                </div>
                <Button 
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(setFile1, setHeaders1, setMapping1)}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <FiX />
                </Button>
              </div>
              
              {headers1.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium mb-2 text-foreground">Column Mapping</h3>
                  {requiredColumns.map(column => (
                    <div key={column} className="mb-2">
                      <label className="block text-xs text-muted-foreground mb-1">{column}</label>
                      <select
                        value={mapping1[column] || ''}
                        onChange={(e) => handleMappingChange(column, e.target.value, setMapping1)}
                        className="w-full h-10 px-3 py-2 rounded-md border border-input bg-background text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      >
                        <option value="">Select column</option>
                        {headers1.map((header, index) => (
                          <option key={index} value={header}>{header}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2 text-foreground">File 2</label>
          {!file2 ? (
            <div 
              {...getRootProps2()} 
              className={cn(
                "border-2 border-dashed border-input rounded-md p-6 text-center hover:border-primary cursor-pointer transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              )}
            >
              <input {...getInputProps2()} />
              <FiUpload className="mx-auto text-3xl mb-2 text-muted-foreground" />
              <p className="text-muted-foreground">Drag & drop an Excel file here, or click to select</p>
            </div>
          ) : (
            <div className="border rounded-md p-4 bg-muted">
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <FiFile className="text-primary mr-2" />
                  <span className="truncate">{file2.name}</span>
                </div>
                <Button 
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(setFile2, setHeaders2, setMapping2)}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <FiX />
                </Button>
              </div>
              
              {headers2.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium mb-2 text-foreground">Column Mapping</h3>
                  {requiredColumns.map(column => (
                    <div key={column} className="mb-2">
                      <label className="block text-xs text-muted-foreground mb-1">{column}</label>
                      <select
                        value={mapping2[column] || ''}
                        onChange={(e) => handleMappingChange(column, e.target.value, setMapping2)}
                        className="w-full h-10 px-3 py-2 rounded-md border border-input bg-[#0f3cc9] text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      >
                        <option value="">Select column</option>
                        {headers2.map((header, index) => (
                          <option key={index} value={header}>{header}</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="text-center">
        <Button 
          type="submit" 
          disabled={loading || !file1 || !file2}
          className="px-6 bg-button"
        >
          {loading ? 'Processing...' : 'Compare Files'}
        </Button>
      </div>
    </form>
  )
}

export default FileUploader 