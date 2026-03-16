import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <p className="text-8xl font-black text-gray-200 mb-4 select-none">404</p>
        <h1 className="text-xl font-bold text-gray-900 mb-2">Page not found</h1>
        <p className="text-gray-500 text-sm mb-8">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm px-5 py-2.5 rounded-lg transition-colors"
          >
            Back to Dashboard
          </Link>
          <a
            href="mailto:support@tracelayer.it.com"
            className="text-sm text-gray-500 hover:text-gray-700 underline underline-offset-2"
          >
            Contact support
          </a>
        </div>
        <div className="mt-8 flex items-center justify-center gap-4 text-xs text-gray-400">
          <Link href="/status" className="hover:text-gray-600">System status</Link>
          <Link href="/" className="hover:text-gray-600">Homepage</Link>
        </div>
      </div>
    </div>
  );
}
