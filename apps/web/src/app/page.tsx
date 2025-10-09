/**
 * Homepage
 *
 * Discovery-focused landing page with:
 * - Hero section with value proposition
 * - Prominent CTA to /opportunities
 * - Navigation links
 * - ThemeToggle
 * - Dark mode support
 */

import Link from 'next/link';
import { ThemeToggle } from '@/components/opportunities/ThemeToggle';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              MicroAppFinder
            </h1>
            <nav className="flex items-center gap-4 sm:gap-6">
              <Link
                href="/dashboard"
                className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/login"
                className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                Sign In
              </Link>
              <ThemeToggle />
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 text-center">
        <div className="space-y-8">
          {/* Main Headline */}
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
            Discover Validated
            <br />
            <span className="text-blue-600 dark:text-blue-400">
              Micro-App Opportunities
            </span>
          </h2>

          {/* Subheadline */}
          <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto leading-relaxed">
            Browse a curated catalog of business opportunities with 6-dimensional scoring.
            <br className="hidden sm:block" />
            Sourced from real pain points on Reddit & HackerNews.
          </p>

          {/* CTA Button */}
          <div className="pt-4">
            <Link
              href="/opportunities"
              className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 dark:bg-blue-500 text-white rounded-lg text-lg font-semibold hover:bg-blue-700 dark:hover:bg-blue-600 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              Explore Opportunities
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 pt-12 sm:pt-16">
            <div className="p-6 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
              <div className="text-3xl mb-3">🎯</div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Problem Severity
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Scored 0-10 based on user frustration and urgency
              </p>
            </div>

            <div className="p-6 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
              <div className="text-3xl mb-3">💰</div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Market Analysis
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Size, competition, and monetization potential
              </p>
            </div>

            <div className="p-6 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
              <div className="text-3xl mb-3">📈</div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Trend Direction
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Growing, stable, or declining market trends
              </p>
            </div>
          </div>

          {/* Secondary CTA */}
          <div className="pt-8">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Already have an account?
            </p>
            <div className="flex gap-4 justify-center">
              <Link
                href="/login"
                className="px-6 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-6 py-2 text-sm font-medium border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                Create Account
              </Link>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 mt-16 sm:mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            © 2025 MicroAppFinder. Discover opportunities from real user pain points.
          </p>
        </div>
      </footer>
    </div>
  );
}
