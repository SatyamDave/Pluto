import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Shield, 
  Zap, 
  Globe, 
  Users, 
  CheckCircle, 
  ArrowRight,
  Github,
  Linkedin,
  CreditCard,
  UserCheck,
  Sparkles,
  TrendingUp
} from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="container-wide py-20 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <Badge variant="secondary" className="mb-4">
              <Sparkles className="w-4 h-4 mr-2" />
              AI-Powered Identity Verification
            </Badge>
            
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
              Your AI-Native
              <span className="gradient-text block">Identity System</span>
            </h1>
            
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
              Create modular, verifiable identity cards for work, finance, and beyond. 
              AI-generated, always up-to-date, and privacy-controlled.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild size="lg" className="btn-primary">
                <Link href="/auth/signin">
                  Get Started Free
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="#features">
                  Learn More
                </Link>
              </Button>
            </div>
          </div>
        </div>
        
        {/* Background decoration */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-72 h-72 bg-primary-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-identity-highlight/10 rounded-full blur-3xl"></div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white dark:bg-gray-900">
        <div className="container-wide px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Modular Identity Cards
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Choose the right identity for every situation. Each card is AI-generated, 
              verifiable, and automatically updated.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Work Identity Card */}
            <Card className="hover-lift hover-glow border-0 shadow-lg">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Users className="w-6 h-6 text-primary-600" />
                </div>
                <CardTitle className="text-xl">Work Identity</CardTitle>
                <CardDescription>
                  Skills, experience, and verified work history
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    AI-verified skills from GitHub
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    LinkedIn experience validation
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Dynamic project portfolio
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Financial Identity Card */}
            <Card className="hover-lift hover-glow border-0 shadow-lg">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-success-100 dark:bg-success-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <CreditCard className="w-6 h-6 text-success-600" />
                </div>
                <CardTitle className="text-xl">Financial Identity</CardTitle>
                <CardDescription>
                  Income proof, creditworthiness, and risk assessment
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Plaid integration for banking
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    AI-powered risk scoring
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Real-time financial health
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Creator Identity Card */}
            <Card className="hover-lift hover-glow border-0 shadow-lg">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-warning-100 dark:bg-warning-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="w-6 h-6 text-warning-600" />
                </div>
                <CardTitle className="text-xl">Creator Identity</CardTitle>
                <CardDescription>
                  Social proof, engagement quality, and authenticity
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Multi-platform analytics
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Bot detection & verification
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Engagement quality scoring
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Civic Identity Card */}
            <Card className="hover-lift hover-glow border-0 shadow-lg">
              <CardHeader className="text-center">
                <div className="w-12 h-12 bg-error-100 dark:bg-error-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <UserCheck className="w-6 h-6 text-error-600" />
                </div>
                <CardTitle className="text-xl">Civic Identity</CardTitle>
                <CardDescription>
                  Human verification and community reputation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Real-human verification
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Community contributions
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    Reputation scoring
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-50 dark:bg-gray-800">
        <div className="container-wide px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Three simple steps to create your AI-powered identity cards
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-primary-600">1</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Connect Your Sources
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Link your GitHub, LinkedIn, and other professional accounts. 
                We securely access your data with your permission.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-primary-600">2</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                AI Processing
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Our AI analyzes your data to extract skills, verify experiences, 
                and generate structured claims with confidence scores.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl font-bold text-primary-600">3</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Share Your Cards
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Generate beautiful, verifiable identity cards. Share them via 
                link, QR code, or embed in your digital presence.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-600">
        <div className="container-wide px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Build Your AI Identity?
          </h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Join thousands of professionals who trust AI Identity Platform 
            for their digital identity needs.
          </p>
          <Button asChild size="lg" variant="secondary">
            <Link href="/auth/signin">
              Start Building Today
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </section>
    </div>
  )
}
