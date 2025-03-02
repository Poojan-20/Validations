import { useState } from 'react'
import FileUploader from './components/FileUploader'
import ProgressBar from './components/ProgressBar'
import ProcessedFiles from './components/ProcessedFiles'
import Header from './components/Header'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'

function App() {
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState({
    step: 'loading',
    percentage: 0,
    stats: {},
    complete: false
  })

  return (
    <div className="min-h-screen bg-#0f3cc9 flex flex-col">
      <Header />
      
      <main className="container mx-auto px-4 py-8 flex-grow">
        <div className="space-y-8">
          {/* File Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle>Reconciliation Tool</CardTitle>
              <CardDescription>
                Upload two Excel files to compare and validate their contents. The system will analyze the data and provide a detailed report of matches, mismatches, and other validation results.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isUploading && (
                <div className="mb-6">
                  <ProgressBar progress={progress} />
                </div>
              )}
              
              <FileUploader 
                setIsUploading={setIsUploading} 
                setProgress={setProgress}
              />
            </CardContent>
          </Card>
          
          {/* Processed Files and Stats Section */}
          <ProcessedFiles />
        </div>
      </main>
      
      <footer className="bg-secondary py-6 mt-12">
        <div className="container mx-auto px-4">
          <p className="text-center text-secondary-foreground">Excel Validator &copy; Made with ❤️ by <a href="https://github.com/Poojan-20" className="underline">Poojan</a> {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  )
}

export default App 