import { ArrowRight, FileText, Image as ImageIcon, ShieldPlus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { PageHeader } from '@/components/page-header';

const items = [
  {
    title: 'Resume Generator',
    description: 'Convert raw resume notes into a generated PDF and preview it immediately.',
    to: '/resume',
    icon: FileText,
  },
  {
    title: 'Image Generator',
    description: 'Run prompt-based image generation with adjustable mode and inference steps.',
    to: '/image',
    icon: ImageIcon,
  },
  {
    title: 'Medical Analyzer',
    description: 'Upload clinical images or reports and inspect structured findings in one place.',
    to: '/medical',
    icon: ShieldPlus,
  },
];

export function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Run your three AI workflows from a single operational workspace."
      />

      <section className="grid gap-4 lg:grid-cols-3">
        {items.map(({ title, description, to, icon: Icon }) => (
          <Link key={to} to={to}>
            <Card className="h-full p-6 transition hover:-translate-y-0.5 hover:border-slate-300">
              <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                <Icon className="h-5 w-5" />
              </div>
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <h2 className="text-lg font-semibold text-ink">{title}</h2>
                  <ArrowRight className="mt-0.5 h-4 w-4 text-slate-400" />
                </div>
                <p className="text-sm text-muted">{description}</p>
              </div>
            </Card>
          </Link>
        ))}
      </section>
    </>
  );
}
