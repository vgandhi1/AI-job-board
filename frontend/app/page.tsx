'use client'

import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { JobInsightCard } from '@/components/JobInsightCard'
import { semanticSearch, JobMatch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function Home() {
  const [query, setQuery] = useState('')
  const [jobs, setJobs] = useState<JobMatch[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    setError(null)
    setHasSearched(true)

    try {
      const results = await semanticSearch(query.trim(), 10)
      setJobs(results)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during search')
      setJobs([])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">AI Job Board</h1>
          <p className="text-muted-foreground">
            Intelligent career agent powered by semantic search and AI analysis
          </p>
        </div>

        {/* Search Bar */}
        <Card className="p-6 mb-8">
          <form onSubmit={handleSearch} className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for jobs... (e.g., 'Senior Python developer with ML experience')"
                className="w-full pl-10 pr-4 py-3 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                disabled={isLoading}
              />
            </div>
            <Button type="submit" disabled={isLoading || !query.trim()}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </form>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="p-4 mb-6 border-destructive bg-destructive/10">
            <p className="text-sm text-destructive">{error}</p>
          </Card>
        )}

        {/* Results */}
        {hasSearched && !isLoading && (
          <div className="mb-4">
            <p className="text-sm text-muted-foreground">
              Found {jobs.length} {jobs.length === 1 ? 'job' : 'jobs'}
            </p>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        {!isLoading && jobs.length === 0 && hasSearched && !error && (
          <Card className="p-12 text-center">
            <p className="text-muted-foreground">No jobs found. Try a different search query.</p>
          </Card>
        )}

        {!isLoading && jobs.length > 0 && (
          <div className="space-y-4">
            {jobs.map((job) => (
              <JobInsightCard
                key={job.id}
                job={job}
                userQuery={query}
                onViewDetails={(jobId) => {
                  console.log('View details for job:', jobId)
                  // You can implement navigation or modal here
                }}
              />
            ))}
          </div>
        )}

        {!hasSearched && (
          <Card className="p-12 text-center">
            <p className="text-muted-foreground mb-4">
              Enter a search query to find jobs using AI-powered semantic search.
            </p>
            <p className="text-sm text-muted-foreground">
              Try searching for skills, experience level, or job requirements in natural language.
            </p>
          </Card>
        )}
      </div>
    </main>
  )
}
