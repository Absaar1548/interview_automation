'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function CandidatePage() {
  const router = useRouter()
  const [userData, setUserData] = useState<any>(null)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token')
    const userType = localStorage.getItem('userType')
    const storedUserData = localStorage.getItem('userData')

    if (!token || userType !== 'candidate') {
      router.push('/login/candidate')
      return
    }

    if (storedUserData) {
      setUserData(JSON.parse(storedUserData))
    }
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userType')
    localStorage.removeItem('userData')
    router.push('/')
  }

  if (!userData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Candidate Dashboard</h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">Welcome, {userData.email}</p>
            </div>
            <div className="flex gap-4">
              <Link href="/" className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
                Home
              </Link>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          <div className="text-center">
            <div className="text-6xl mb-4">🎯</div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">Welcome to Your Interview Portal</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-8">
              Your interview dashboard is ready. You can view your interview status and access your assessments here.
            </p>
            
            <div className="grid md:grid-cols-2 gap-6 mt-8">
              <div className="p-6 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Interview Status</h3>
                <p className="text-gray-600 dark:text-gray-300">Check your interview progress and results</p>
              </div>
              <div className="p-6 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Take Interview</h3>
                <p className="text-gray-600 dark:text-gray-300">Start or continue your interview assessment</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
