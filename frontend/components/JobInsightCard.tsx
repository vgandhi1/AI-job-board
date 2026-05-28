'use client'

import React, { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { MapPin, DollarSign, Calendar, ChevronRight, Sparkles } from 'lucide-react'
import { JobMatch, analyzeJobFit } from '@/lib/api'
import { cn } from '@/lib/utils'

interface JobInsightCardProps {
  job: JobMatch
  userQuery: string
  onViewDetails?: (jobId: number) => void
}

export function JobInsightCard({ job, userQuery, onViewDetails }: JobInsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [fitAnalysis, setFitAnalysis] = useState<{ analysis_summary: string; pros: string[]; cons: string[] } | null>(null)
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false)

  const matchPercentage = Math.round(job.match_score * 100)
  const matchVariant = matchPercentage >= 90 ? 'success' : matchPercentage >= 70 ? 'warning' : 'default'

  const formatSalary = () => {
    if (!job.salary_min && !job.salary_max) return null
    if (job.salary_min && job.salary_max) {
      return `${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()} ${job.salary_currency}`
    }
    if (job.salary_min) {
      return `${job.salary_min.toLocaleString}+ ${job.salary_currency}`
    }
    return `Up to ${job.salary_max?.toLocaleString()} ${job.salary_currency}`
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  const handleViewDetails = async () => {
    if (!isExpanded && !fitAnalysis) {
      setIsLoadingAnalysis(true)
      try {
        const analysis = await analyzeJobFit(userQuery, job.id)
        setFitAnalysis(analysis.fit_analysis)
        setIsExpanded(true)
      } catch (error) {
        console.error('Failed to load analysis:', error)
        // Fallback: still expand but without analysis
        setIsExpanded(true)
      } finally {
        setIsLoadingAnalysis(false)
      }
    } else {
      setIsExpanded(!isExpanded)
    }
    
    if (onViewDetails) {
      onViewDetails(job.id)
    }
  }

  return (
    <Card 
      className={cn(
        "transition-all duration-200 hover:border-primary/50 hover:shadow-md",
        isExpanded && "border-primary/30 shadow-lg"
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-xl mb-1 line-clamp-1">{job.title}</CardTitle>
            <CardDescription className="text-base font-medium text-foreground/80">
              {job.company}
            </CardDescription>
          </div>
          <Badge variant={matchVariant} className="shrink-0">
            {matchPercentage}% Match
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {!isExpanded ? (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {job.description}
          </p>
        ) : (
          <div className="space-y-4">
            {isLoadingAnalysis ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : fitAnalysis ? (
              <div className="space-y-4">
                <div className="flex items-start gap-2">
                  <Sparkles className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium mb-2">AI Analysis</p>
                    <p className="text-sm text-muted-foreground mb-3">
                      {fitAnalysis.analysis_summary}
                    </p>
                    
                    {fitAnalysis.pros.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">Strengths:</p>
                        <ul className="text-xs text-muted-foreground space-y-1">
                          {fitAnalysis.pros.map((pro, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-green-600 dark:text-green-500 mt-0.5">•</span>
                              <span>{pro}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {fitAnalysis.cons.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 mb-1">Considerations:</p>
                        <ul className="text-xs text-muted-foreground space-y-1">
                          {fitAnalysis.cons.map((con, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-amber-600 dark:text-amber-500 mt-0.5">•</span>
                              <span>{con}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <p className="text-sm font-medium mb-2">Full Description</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {job.description}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {job.description}
              </p>
            )}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground pt-2">
          {job.location && (
            <div className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4" />
              <span>{job.location}</span>
            </div>
          )}
          {formatSalary() && (
            <div className="flex items-center gap-1.5">
              <DollarSign className="h-4 w-4" />
              <span>{formatSalary()}</span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <Calendar className="h-4 w-4" />
            <span>Posted {formatDate(job.posted_at)}</span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-2">
        <Button
          variant="outline"
          className="w-full group"
          onClick={handleViewDetails}
          disabled={isLoadingAnalysis}
        >
          {isLoadingAnalysis ? (
            'Analyzing...'
          ) : isExpanded ? (
            'Show Less'
          ) : (
            <>
              View Details
              <ChevronRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
