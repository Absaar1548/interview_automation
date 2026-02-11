import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 gap-4">
      <h1 className="text-4xl font-bold mb-8">AI Interview Automation</h1>
      <div className="grid grid-cols-1 gap-4 text-center">
        <Link href="/login" className="p-4 border rounded hover:bg-gray-100 dark:hover:bg-gray-800">Login</Link>
        <Link href="/hr/dashboard" className="p-4 border rounded hover:bg-gray-100 dark:hover:bg-gray-800">HR Dashboard</Link>
        <Link href="/candidate" className="p-4 border rounded hover:bg-gray-100 dark:hover:bg-gray-800">Candidate Portal</Link>
        <Link href="/interview" className="p-4 border rounded hover:bg-gray-100 dark:hover:bg-gray-800">Interview Interface</Link>
        <Link href="/summary" className="p-4 border rounded hover:bg-gray-100 dark:hover:bg-gray-800">Summary</Link>
      </div>
    </main>
  )
}
