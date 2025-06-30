import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Briefcase } from 'lucide-react'

const JobsPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Jobs</h1>
          <p className="text-gray-600 mt-2">Browse and search for job opportunities</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Job Search</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12">
              <Briefcase className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Jobs Page Coming Soon</h3>
              <p className="text-gray-500">
                This page will display job listings with advanced search and filtering capabilities.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default JobsPage

