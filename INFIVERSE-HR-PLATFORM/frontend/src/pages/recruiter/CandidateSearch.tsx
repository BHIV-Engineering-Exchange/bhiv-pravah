import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import toast from 'react-hot-toast'
import { searchCandidates, getRecruiterJobs, getCandidateSuggestionsResponse, type CandidateProfile } from '../../services/api'
import Table from '../../components/Table'
import Loading from '../../components/Loading'
import AutocompleteSearch from '../../components/AutocompleteSearch'

// MultiSelect Dropdown Component
interface MultiSelectDropdownProps {
  label: string
  options: string[]
  selected: string[]
  onChange: (selected: string[]) => void
  placeholder?: string
  chipColor?: 'gray' | 'green'
}

function MultiSelectDropdown({ label, options, selected, onChange, placeholder = 'Select options', chipColor = 'gray' }: MultiSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const toggleOption = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter(item => item !== option))
    } else {
      onChange([...selected, option])
    }
  }

  const chipColors = {
    gray: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
    green: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  }

  return (
    <div className="space-y-3" ref={dropdownRef}>
      <label className="text-sm font-semibold text-gray-300">
        {label}
      </label>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-4 py-2.5 text-left bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent flex items-center justify-between text-gray-700 dark:text-gray-300"
        >
          <span className={selected.length === 0 ? 'text-gray-400' : ''}>
            {selected.length === 0 ? placeholder : `${selected.length} selected`}
          </span>
          <svg
            className={`w-5 h-5 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            <div className="p-2 space-y-1">
              {options.map((option) => (
                <label
                  key={option}
                  className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700/50 p-2 rounded transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(option)}
                    onChange={() => toggleOption(option)}
                    className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500 focus:ring-2"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{option}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Selected Options as Chips */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {selected.map((item) => (
            <span
              key={item}
              className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${chipColors[chipColor]}`}
            >
              {item}
              <button
                type="button"
                onClick={() => onChange(selected.filter(s => s !== item))}
                className="hover:opacity-70 transition-opacity"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function CandidateSearch() {
  const navigate = useNavigate()
  const location = useLocation()
  const [candidates, setCandidates] = useState<CandidateProfile[]>([])
  const [jobs, setJobs] = useState<{ id: string; title?: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [searchClicked, setSearchClicked] = useState(false)
  const [hasApplicants, setHasApplicants] = useState<boolean | null>(null)

  // Search filters (prefill from navbar global search)
  const [searchQuery, setSearchQuery] = useState(() => (location.state as { searchQuery?: string })?.searchQuery || '')
  const [selectedJobId, setSelectedJobId] = useState<string>('all')
  const [experienceFilter, setExperienceFilter] = useState('any')
  const [seniorityFilter, setSeniorityFilter] = useState<string[]>([])
  const [educationFilter, setEducationFilter] = useState<string[]>([])
  const [locationFilter, setLocationFilter] = useState<string[]>([])
  const [skillsFilter, setSkillsFilter] = useState<string[]>([])
  const [valuesScore, setValuesScore] = useState(3.0)
  const [statusFilter, setStatusFilter] = useState<string[]>(['applied'])
  const [sortBy, setSortBy] = useState('ai_score')

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      const jobsData = await getRecruiterJobs()
      setJobs(jobsData)
    } catch (error) {
      console.error('Failed to load recruiter jobs:', error)
    }
  }

  const fetchCandidateSuggestions = useCallback(async (q: string) => {
    const { suggestions, has_applicants } = await getCandidateSuggestionsResponse(q, 10)
    setHasApplicants(has_applicants ?? null)
    return suggestions
  }, [])

  const handleSearch = async () => {
    setLoading(true)
    setSearchClicked(true)

    try {
      const filters: any = {}
      
      if (searchQuery.trim()) {
        filters.search = searchQuery.trim()
      }
      
      if (selectedJobId !== 'all') {
        filters.job_id = selectedJobId
      }
      
      if (skillsFilter.length) {
        filters.skills = skillsFilter.join(',')
      }
      
      if (locationFilter.length) {
        filters.location = locationFilter.join(',')
      }
      
      if (experienceFilter !== 'any') {
        if (experienceFilter === '0-1') {
          filters.experience_min = 0
          filters.experience_max = 1
        } else if (experienceFilter === '1-3') {
          filters.experience_min = 1
          filters.experience_max = 3
        } else if (experienceFilter === '3-5') {
          filters.experience_min = 3
          filters.experience_max = 5
        } else if (experienceFilter === '5-8') {
          filters.experience_min = 5
          filters.experience_max = 8
        } else if (experienceFilter === '8+') {
          filters.experience_min = 8
        }
      }

      if (educationFilter.length > 0) {
        filters.education_level = educationFilter.join(',')
      }

      if (seniorityFilter.length > 0) {
        filters.seniority_level = seniorityFilter.join(',')
      }

      if (statusFilter.length > 0) {
        filters.status = statusFilter.join(',')
      }

      const results = await searchCandidates(searchQuery || '', filters)
      setCandidates(results.candidates ?? [])
      
      if (!results.candidates?.length) {
        toast('No candidates found matching your criteria', { icon: 'ℹ' })
      } else {
        toast.success(`Found ${results.candidates.length} candidates`)
      }
    } catch (error) {
      console.error('Search error:', error)
      toast.error('Failed to search candidates')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      applied: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      screened: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      shortlisted: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
      interviewed: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      offered: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
      hired: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    }
    return colors[status.toLowerCase()] || colors.applied
  }

  const clearAllFilters = () => {
    setSearchQuery('')
    setSelectedJobId('all')
    setExperienceFilter('any')
    setSeniorityFilter([])
    setEducationFilter([])
    setLocationFilter([])
    setSkillsFilter([])
    setValuesScore(3.0)
    setStatusFilter(['applied'])
    setSortBy('ai_score')
    setSearchClicked(false)
    setCandidates([])
  }

  const getActiveFiltersCount = () => {
    let count = 0
    if (searchQuery.trim()) count++
    if (selectedJobId !== 'all') count++
    if (experienceFilter !== 'any') count++
    if (seniorityFilter.length > 0) count++
    if (educationFilter.length > 0) count++
    if (locationFilter.length > 0) count++
    if (skillsFilter.length > 0) count++
    if (valuesScore !== 3.0) count++
    if (statusFilter.length !== 1 || statusFilter[0] !== 'applied') count++
    if (sortBy !== 'ai_score') count++
    return count
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <h1 className="page-title">Advanced Candidate Search & Filtering</h1>
        <p className="page-subtitle">Search and filter candidates using AI-powered semantic search and advanced filters</p>
      </div>

      {/* Search Controls */}
      <div className="card">
        {/* Main Search Bar */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="md:col-span-1">
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search Candidates
            </label>
            <div className="relative">
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 z-10 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <AutocompleteSearch
                value={searchQuery}
                onChange={setSearchQuery}
                fetchSuggestions={fetchCandidateSuggestions}
                getSuggestionLabel={(s) => `${(s as { name?: string }).name || ''} - ${(s as { email?: string }).email || ''}`}
                placeholder="Search by name or email"
                inputClassName="input-field pl-10"
                minLength={1}
                debounceMs={250}
                maxSuggestions={10}
                emptyOptionLabel={hasApplicants === false ? 'No applicants yet' : hasApplicants === true ? 'No matching candidates' : undefined}
                onEmptySelect={() => toast(hasApplicants === false ? 'You have no applicants yet.' : 'No candidates match your search. Try different terms.', { icon: 'ℹ' })}
              />
            </div>
          </div>
          <div className="md:col-span-1">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Filter by Job
            </label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="input-field w-full"
            >
              <option value="all">All Jobs</option>
              {jobs.length === 0 ? (
                <option value="" disabled>No jobs posted</option>
              ) : (
                jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title || 'Untitled'} - {j.id}
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        {/* Advanced Filters */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="section-title flex items-center gap-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Advanced Filters
            </h3>
          </div>
          
          {/* Filter Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Experience Level */}
            <div className="space-y-3">
            <label className="text-sm font-semibold text-gray-300">
              Experience Level
            </label>
              <select
                value={experienceFilter}
                onChange={(e) => setExperienceFilter(e.target.value)}
                className="input-field"
              >
                <option value="any">Any Experience</option>
                <option value="0-2 years">0-2 years</option>
                <option value="2-5 years">2-5 years</option>
                <option value="5+ years">5+ years</option>
              </select>
            </div>

            {/* Education Level */}
            <MultiSelectDropdown
              label="Education Level"
              options={['Bachelors', 'Masters', 'PhD', 'Diploma']}
              selected={educationFilter}
              onChange={setEducationFilter}
              placeholder="Choose education level"
              chipColor="gray"
            />

            {/* Technical Skills */}
            <MultiSelectDropdown
              label="Technical Skills"
              options={['Python', 'JavaScript', 'Java', 'React', 'AWS', 'Docker', 'SQL']}
              selected={skillsFilter}
              onChange={setSkillsFilter}
              placeholder="Choose technical skills"
              chipColor="gray"
            />

            {/* Seniority Level */}
            <MultiSelectDropdown
              label="Seniority Level"
              options={['Entry-level', 'Mid-level', 'Senior', 'Lead']}
              selected={seniorityFilter}
              onChange={setSeniorityFilter}
              placeholder="Choose seniority level"
              chipColor="gray"
            />

            {/* Location */}
            <MultiSelectDropdown
              label="Location"
              options={['Mumbai', 'Bangalore', 'Delhi', 'Pune', 'Chennai', 'Remote']}
              selected={locationFilter}
              onChange={setLocationFilter}
              placeholder="Choose locations"
              chipColor="gray"
            />

            {/* Values Score */}
            <div className="space-y-3">
              <label className="text-sm font-semibold text-gray-300">
                Minimum Values Score: <span className="text-green-500 font-bold">{valuesScore.toFixed(1)}</span>
              </label>
              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="0.1"
                  value={valuesScore}
                  onChange={(e) => setValuesScore(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gradient-to-r from-red-200 to-green-200 dark:from-red-900/30 dark:to-green-900/30 rounded-lg appearance-none cursor-pointer accent-red-500"
                />
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
                  <span>1.0</span>
                  <span>3.0</span>
                  <span>5.0</span>
                </div>
              </div>
            </div>

            {/* Candidate Status */}
            <MultiSelectDropdown
              label="Candidate Status"
              options={['applied', 'screened', 'interviewed', 'offered', 'hired']}
              selected={statusFilter}
              onChange={setStatusFilter}
              placeholder="Choose status"
              chipColor="gray"
            />

            {/* Sort By */}
            <div className="space-y-3">
              <label className="text-sm font-semibold text-gray-300">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="input-field"
              >
                <option value="ai_score">AI Score (High to Low)</option>
                <option value="experience">Experience (High to Low)</option>
                <option value="values">Values Score (High to Low)</option>
                <option value="name">Name (A-Z)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleSearch}
            disabled={loading}
            className="group flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-6 py-2.5 rounded-lg font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-md shadow-green-500/25 hover:shadow-lg hover:shadow-green-500/40 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Searching...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Search</span>
              </>
            )}
          </button>
          {getActiveFiltersCount() > 0 && (
            <button
              onClick={clearAllFilters}
              className="px-4 py-2.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium text-sm transition-all duration-200 flex items-center gap-1.5 hover:scale-[1.02] active:scale-[0.98]"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span>Clear</span>
            </button>
          )}
        </div>

      </div>

      {/* Search Results */}
      {searchClicked && (
        <div className="card">
          {loading ? (
            <Loading message="Searching candidates..." />
          ) : candidates.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-gray-500 dark:text-gray-400 text-lg">
                {hasApplicants === false ? 'You have no applicants yet' : 'No candidates found matching your criteria'}
              </p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                {hasApplicants === false ? 'Candidates will appear here once they apply to your jobs.' : 'Try adjusting your search filters'}
              </p>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="section-title">Search Results</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Found {candidates.length} candidates matching your criteria
                  </p>
                </div>
              </div>
              <Table
                columns={['Name', 'Email', 'Experience', 'Location', 'Skills', 'Status', 'Actions']}
                data={candidates}
                renderRow={(candidate: any) => (
                  <>
                    <td className="font-semibold text-gray-900 dark:text-white">{candidate.name || 'N/A'}</td>
                    <td className="text-gray-600 dark:text-gray-400">{candidate.email || 'N/A'}</td>
                    <td className="text-gray-600 dark:text-gray-400">{candidate.experience_years || 0} years</td>
                    <td className="text-gray-600 dark:text-gray-400">{candidate.location || 'N/A'}</td>
                    <td>
                      <div className="flex flex-wrap gap-1 max-w-[200px]">
                        {(candidate.skills || candidate.technical_skills || '').split(',').slice(0, 3).map((skill: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs">
                            {skill.trim()}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(candidate.status || 'applied')}`}>
                        {(candidate.status || 'applied').charAt(0).toUpperCase() + (candidate.status || 'applied').slice(1)}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => navigate(`/recruiter/feedback/${candidate.id || candidate.candidate_id}`)}
                        className="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 font-semibold text-sm"
                      >
                        View Details →
                      </button>
                    </td>
                  </>
                )}
              />
            </>
          )}
        </div>
      )}
    </div>
  )
}
