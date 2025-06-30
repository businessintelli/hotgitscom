import { useState, useEffect } from 'react'
import { useAuth } from '../../App'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts'
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Briefcase, 
  Target, 
  Clock,
  DollarSign,
  Eye,
  Send,
  CheckCircle,
  XCircle,
  Calendar,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react'

const AnalyticsPage = () => {
  const { user } = useAuth()
  const [timeRange, setTimeRange] = useState('30d')
  const [isLoading, setIsLoading] = useState(false)

  // Sample data - in real app, this would come from API
  const candidateMetrics = {
    overview: {
      profileViews: { value: 1247, change: 12.5, trend: 'up' },
      applications: { value: 23, change: -5.2, trend: 'down' },
      responses: { value: 8, change: 33.3, trend: 'up' },
      interviews: { value: 4, change: 100, trend: 'up' }
    },
    applicationTrend: [
      { month: 'Jan', applications: 12, responses: 3, interviews: 1 },
      { month: 'Feb', applications: 18, responses: 5, interviews: 2 },
      { month: 'Mar', applications: 15, responses: 4, interviews: 1 },
      { month: 'Apr', applications: 22, responses: 7, interviews: 3 },
      { month: 'May', applications: 28, responses: 9, interviews: 4 },
      { month: 'Jun', applications: 23, responses: 8, interviews: 4 }
    ],
    skillsMatch: [
      { skill: 'JavaScript', match: 95, demand: 85 },
      { skill: 'React', match: 90, demand: 80 },
      { skill: 'Python', match: 85, demand: 90 },
      { skill: 'Node.js', match: 80, demand: 75 },
      { skill: 'SQL', match: 75, demand: 70 }
    ],
    industryInterest: [
      { name: 'Technology', value: 45, color: '#3B82F6' },
      { name: 'Finance', value: 25, color: '#10B981' },
      { name: 'Healthcare', value: 15, color: '#F59E0B' },
      { name: 'Education', value: 10, color: '#EF4444' },
      { name: 'Other', value: 5, color: '#8B5CF6' }
    ]
  }

  const recruiterMetrics = {
    overview: {
      activeJobs: { value: 12, change: 20, trend: 'up' },
      totalApplications: { value: 456, change: 15.3, trend: 'up' },
      hires: { value: 8, change: 60, trend: 'up' },
      timeToHire: { value: 18, change: -12.5, trend: 'down' }
    },
    hiringFunnel: [
      { stage: 'Applications', count: 456, percentage: 100 },
      { stage: 'Screening', count: 123, percentage: 27 },
      { stage: 'Interview', count: 45, percentage: 10 },
      { stage: 'Final Round', count: 18, percentage: 4 },
      { stage: 'Offer', count: 12, percentage: 3 },
      { stage: 'Hired', count: 8, percentage: 2 }
    ],
    jobPerformance: [
      { job: 'Senior Developer', applications: 89, hires: 2, quality: 4.5 },
      { job: 'Product Manager', applications: 67, hires: 1, quality: 4.2 },
      { job: 'Data Scientist', applications: 45, hires: 1, quality: 4.8 },
      { job: 'UX Designer', applications: 34, hires: 2, quality: 4.3 },
      { job: 'DevOps Engineer', applications: 28, hires: 1, quality: 4.6 }
    ],
    monthlyHires: [
      { month: 'Jan', hires: 3, cost: 12000 },
      { month: 'Feb', hires: 5, cost: 18000 },
      { month: 'Mar', hires: 4, cost: 15000 },
      { month: 'Apr', hires: 6, cost: 22000 },
      { month: 'May', hires: 7, cost: 25000 },
      { month: 'Jun', hires: 8, cost: 28000 }
    ]
  }

  const metrics = user?.role === 'candidate' ? candidateMetrics : recruiterMetrics

  const MetricCard = ({ title, value, change, trend, icon: Icon, suffix = '' }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">
              {value}{suffix}
            </p>
            <div className="flex items-center mt-1">
              {trend === 'up' ? (
                <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
              )}
              <span className={`text-sm ${trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                {Math.abs(change)}%
              </span>
              <span className="text-sm text-gray-500 ml-1">vs last period</span>
            </div>
          </div>
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <Icon className="w-6 h-6 text-blue-600" />
          </div>
        </div>
      </CardContent>
    </Card>
  )

  const CandidateAnalytics = () => (
    <div className="space-y-6">
      {/* Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Profile Views"
          value={metrics.overview.profileViews.value}
          change={metrics.overview.profileViews.change}
          trend={metrics.overview.profileViews.trend}
          icon={Eye}
        />
        <MetricCard
          title="Applications Sent"
          value={metrics.overview.applications.value}
          change={metrics.overview.applications.change}
          trend={metrics.overview.applications.trend}
          icon={Send}
        />
        <MetricCard
          title="Responses Received"
          value={metrics.overview.responses.value}
          change={metrics.overview.responses.change}
          trend={metrics.overview.responses.trend}
          icon={CheckCircle}
        />
        <MetricCard
          title="Interviews"
          value={metrics.overview.interviews.value}
          change={metrics.overview.interviews.change}
          trend={metrics.overview.interviews.trend}
          icon={Users}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Application Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Application Activity</CardTitle>
            <CardDescription>Your job search progress over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics.applicationTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="applications" stroke="#3B82F6" strokeWidth={2} />
                <Line type="monotone" dataKey="responses" stroke="#10B981" strokeWidth={2} />
                <Line type="monotone" dataKey="interviews" stroke="#F59E0B" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Industry Interest */}
        <Card>
          <CardHeader>
            <CardTitle>Industry Focus</CardTitle>
            <CardDescription>Distribution of your job applications</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={metrics.industryInterest}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {metrics.industryInterest.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Skills Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Skills Match Analysis</CardTitle>
          <CardDescription>How your skills align with market demand</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics.skillsMatch}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="skill" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="match" fill="#3B82F6" name="Your Match %" />
              <Bar dataKey="demand" fill="#10B981" name="Market Demand %" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )

  const RecruiterAnalytics = () => (
    <div className="space-y-6">
      {/* Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Active Jobs"
          value={metrics.overview.activeJobs.value}
          change={metrics.overview.activeJobs.change}
          trend={metrics.overview.activeJobs.trend}
          icon={Briefcase}
        />
        <MetricCard
          title="Total Applications"
          value={metrics.overview.totalApplications.value}
          change={metrics.overview.totalApplications.change}
          trend={metrics.overview.totalApplications.trend}
          icon={Users}
        />
        <MetricCard
          title="Successful Hires"
          value={metrics.overview.hires.value}
          change={metrics.overview.hires.change}
          trend={metrics.overview.hires.trend}
          icon={CheckCircle}
        />
        <MetricCard
          title="Avg. Time to Hire"
          value={metrics.overview.timeToHire.value}
          change={metrics.overview.timeToHire.change}
          trend={metrics.overview.timeToHire.trend}
          icon={Clock}
          suffix=" days"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hiring Funnel */}
        <Card>
          <CardHeader>
            <CardTitle>Hiring Funnel</CardTitle>
            <CardDescription>Candidate progression through hiring stages</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metrics.hiringFunnel} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="stage" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="count" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monthly Hires & Cost */}
        <Card>
          <CardHeader>
            <CardTitle>Hiring Trends</CardTitle>
            <CardDescription>Monthly hires and recruitment costs</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics.monthlyHires}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="hires"
                  stackId="1"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.6}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="cost"
                  stroke="#F59E0B"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Job Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Job Performance Analysis</CardTitle>
          <CardDescription>Applications and hiring success by job posting</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {metrics.jobPerformance.map((job, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{job.job}</h4>
                  <div className="flex items-center space-x-4 mt-1">
                    <span className="text-sm text-gray-500">
                      {job.applications} applications
                    </span>
                    <span className="text-sm text-gray-500">
                      {job.hires} hires
                    </span>
                    <Badge variant="secondary">
                      {((job.hires / job.applications) * 100).toFixed(1)}% success rate
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="text-right">
                    <div className="text-sm font-medium">Quality Score</div>
                    <div className="text-lg font-bold text-blue-600">{job.quality}/5.0</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const handleRefresh = () => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => setIsLoading(false), 1000)
  }

  const handleExport = () => {
    // Simulate export functionality
    alert('Analytics data exported successfully!')
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
            <p className="text-gray-600 mt-2">
              {user?.role === 'candidate' 
                ? "Track your job search progress and optimize your strategy" 
                : "Monitor your recruitment performance and hiring metrics"
              }
            </p>
          </div>
          
          <div className="flex items-center space-x-4 mt-4 sm:mt-0">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
                <SelectItem value="1y">Last year</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            
            <Button variant="outline" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Analytics Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="detailed">Detailed Analysis</TabsTrigger>
            <TabsTrigger value="insights">AI Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {user?.role === 'candidate' ? <CandidateAnalytics /> : <RecruiterAnalytics />}
          </TabsContent>

          <TabsContent value="detailed" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Detailed Analytics</CardTitle>
                <CardDescription>
                  In-depth analysis and custom reports
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <BarChart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Advanced Analytics</h3>
                  <p className="text-gray-500 mb-4">
                    Detailed analytics with custom date ranges, filters, and export options.
                  </p>
                  <Button>
                    <Filter className="w-4 h-4 mr-2" />
                    Configure Filters
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="insights" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>AI-Powered Insights</CardTitle>
                <CardDescription>
                  Intelligent recommendations based on your data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <Target className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-900">Optimization Opportunity</h4>
                        <p className="text-blue-700 text-sm mt-1">
                          {user?.role === 'candidate' 
                            ? "Your response rate could improve by 25% by optimizing your application timing. Consider applying on Tuesday-Thursday between 10-11 AM."
                            : "Your time-to-hire could be reduced by 30% by implementing automated screening for junior positions."
                          }
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <TrendingUp className="w-5 h-5 text-green-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-green-900">Positive Trend</h4>
                        <p className="text-green-700 text-sm mt-1">
                          {user?.role === 'candidate' 
                            ? "Your profile views have increased by 45% this month. Your recent skill updates are attracting more attention."
                            : "Your candidate quality score has improved by 20% this quarter. Your refined job descriptions are attracting better matches."
                          }
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <Clock className="w-5 h-5 text-yellow-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-yellow-900">Action Recommended</h4>
                        <p className="text-yellow-700 text-sm mt-1">
                          {user?.role === 'candidate' 
                            ? "Update your skills section to include 'Machine Learning' - it's mentioned in 60% of jobs you're interested in."
                            : "Consider posting your Data Scientist role again with updated requirements - similar roles are seeing 40% more applications."
                          }
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default AnalyticsPage

