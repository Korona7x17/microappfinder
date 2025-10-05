import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="max-w-5xl w-full">
        <h1 className="text-4xl font-bold text-center mb-4">
          MicroAppFinder
        </h1>
        <p className="text-xl text-center text-muted-foreground mb-8">
          Discover unmet demand for micro apps
        </p>
        <div className="text-center space-y-4">
          <p className="text-sm text-muted-foreground mb-4">
            Scan communities for pain points, cluster demand signals, and generate shippable micro-app briefs.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/login"
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="px-6 py-3 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50 font-medium"
            >
              Create Account
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
