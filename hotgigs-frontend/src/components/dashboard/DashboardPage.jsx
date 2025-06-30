import { useAuth } from '../../App'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Briefcase, 
  Users, 
  TrendingUp, 
  Target,
  Plus,
  Search,
  BarChart3,
  Clock
} from 'lucide-react'

const DashboardPage = () => {
  const { user } = useAuth()

  const candidateStats = [
    { title: 'Applications Sent', value: '12', icon: Briefcase, color: 'text-blue-600' },
    { title: 'Profile Views', value: '48', icon: Users, color: 'text-green-600' },
    { title: 'Match Score Avg', value: '85%', icon: Target, color: 'text-purple-600' },
    { title: 'Response Rate', value: '23%', icon: TrendingUp, color: 'text-orange-600' }
  ]

  const recruiterStats = [
    { title: 'Active Jobs', value: '8', icon: Briefcase, color: 'text-blue-600' },
    { title: 'Applications', value: '156', icon: Users, color: 'text-green-600' },
    { title: 'Interviews', value: '24', icon: Clock, color: 'text-purple-600' },
    { title: 'Hires This Month', value: '3', icon: TrendingUp, color: 'text-orange-600' }
  ]

  const stats = user?.role === 'candidate' ? candidateStats : recruiterStats

  const recentActivity = [
    {
      type: 'application',
      title: 'Applied to Senior Developer at TechCorp',
      time: '2 hours ago',
      status: 'pending'
    },
    {
      type: 'match',
      title: 'New job match: Data Scientist at AI Labs',
      time: '5 hours ago',
      status: 'new'
    },
    {
      type: 'view',
      title: 'Your profile was viewed by InnovateTech',
      time: '1 day ago',
      status: 'info'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.email?.split('@')[0]}!
          </h1>
          <p className="text-gray-600 mt-2">
            {user?.role === 'candidate' 
              ? "Here's your job search overview" 
              : "Here's your recruitment dashboard"
            }
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <Card key={index}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                      <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                    </div>
                    <Icon className={`w-8 h-8 ${stat.color}`} />
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>
                  {user?.role === 'candidate' 
                    ? "Get started with your job search" 
                    : "Manage your recruitment process"
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {user?.role === 'candidate' ? (
                  <>
                    <Button className="w-full justify-start" variant="outline">
                      <Search className="mr-2 w-4 h-4" />
                      Browse Jobs
                    </Button>
                    <Button className="w-full justify-start" variant="outline">
                      <Target className="mr-2 w-4 h-4" />
                      AI Job Matching
                    </Button>
                    <Button className="w-full justify-start" variant="outline">
                      <BarChart3 className="mr-2 w-4 h-4" />
                      View Analytics
                    </Button>
                  </>
                ) : (
                  <>
                    <Button className="w-full justify-start" variant="outline">
                      <Plus className="mr-2 w-4 h-4" />
                      Post New Job
                    </Button>
                    <Button className="w-full justify-start" variant="outline">
                      <Users className="mr-2 w-4 h-4" />
                      Find Candidates
                    </Button>
                    <Button className="w-full justify-start" variant="outline">
                      <BarChart3 className="mr-2 w-4 h-4" />
                      View Analytics
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>
                  Your latest updates and notifications
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-4 p-4 border rounded-lg">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <Briefcase className="w-4 h-4 text-blue-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">
                          {activity.title}
                        </p>
                        <p className="text-sm text-gray-500">{activity.time}</p>
                      </div>
                      <div className="flex-shrink-0">
                        <Badge 
                          variant={activity.status === 'new' ? 'default' : 'secondary'}
                        >
                          {activity.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Role-specific content */}
        {user?.role === 'candidate' && (
          <div className="mt-8">
            <Card>
              <CardHeader>
                <CardTitle>Recommended Jobs</CardTitle>
                <CardDescription>
                  Jobs that match your profile and preferences
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">
                    Upload your resume to get personalized job recommendations
                  </p>
                  <Button className="mt-4">
                    Upload Resume
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {user?.role === 'recruiter' && (
          <div className="mt-8">
            <Card>
              <CardHeader>
                <CardTitle>Top Candidates</CardTitle>
                <CardDescription>
                  Candidates that match your job requirements
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">
                    Post a job to start finding qualified candidates
                  </p>
                  <Button className="mt-4">
                    Post Job
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardPage

