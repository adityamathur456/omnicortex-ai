import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/card';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="max-w-md p-8 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-400">404</p>
        <h1 className="mt-3 text-2xl font-semibold text-ink">Page not found</h1>
        <p className="mt-2 text-sm text-muted">
          The route you requested does not exist in this workspace.
        </p>
        <Link to="/dashboard" className="mt-6 inline-flex">
          <span className="inline-flex h-11 items-center justify-center rounded-lg bg-ink px-4 text-sm font-medium text-white transition hover:bg-slate-800">
            Back to dashboard
          </span>
        </Link>
      </Card>
    </div>
  );
}
