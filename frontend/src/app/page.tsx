'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-4 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            Interview Automation Platform
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mt-6">
            Revolutionize your hiring process with AI-powered interviews. 
            Streamline candidate assessments, automate evaluations, and make data-driven hiring decisions.
          </p>
        </div>

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-8 mb-16 max-w-5xl mx-auto">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">AI-Powered Interviews</h3>
            <p className="text-gray-600 dark:text-gray-300">
              Conduct intelligent interviews with automated question generation and real-time evaluation.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Fast & Efficient</h3>
            <p className="text-gray-600 dark:text-gray-300">
              Save time with automated scheduling, assessments, and candidate evaluation processes.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Data-Driven Insights</h3>
            <p className="text-gray-600 dark:text-gray-300">
              Get comprehensive analytics and insights to make informed hiring decisions.
            </p>
          </div>
        </div>

        {/* Login Options */}
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Welcome Back!</h2>
            <p className="text-gray-600 dark:text-gray-300">Choose your login option to continue</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Candidate Login Card */}
            <div 
              onClick={() => router.push('/login/candidate')}
              className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all cursor-pointer transform hover:scale-105 border-2 border-transparent hover:border-indigo-500"
            >
              <div className="text-center">
                <div className="text-6xl mb-4">👤</div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Candidate Login</h3>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Access your interview dashboard and start your assessment
                </p>
                <button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                  Login as Candidate
                </button>
              </div>
            </div>

            {/* Admin Login Card */}
            <div 
              onClick={() => router.push('/login/admin')}
              className="bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all cursor-pointer transform hover:scale-105 border-2 border-transparent hover:border-purple-500"
            >
              <div className="text-center">
                <div className="text-6xl mb-4">👔</div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Admin Login</h3>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                  Manage candidates, schedule interviews, and review assessments
                </p>
                <button className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
                  Login as Admin
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-16 text-gray-500 dark:text-gray-400">
          <p>© 2024 Interview Automation Platform. All rights reserved.</p>
        </div>
      </div>
    </main>
  )
}
