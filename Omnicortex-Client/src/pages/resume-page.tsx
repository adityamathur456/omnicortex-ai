import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Clock3, Download, ExternalLink, FileText, History } from 'lucide-react';
import toast from 'react-hot-toast';
import { generateResume } from '@/api/resume';
import { EmptyState } from '@/components/empty-state';
import { FormField } from '@/components/form-field';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import {
  appendResumeHistoryItem,
  getResumePageState,
  setResumePageState,
} from '@/store/generation-history';
import type { ResumeHistoryItem, ResumeResponse } from '@/types';
import { downloadFromUrl, getFilenameFromUrl } from '@/utils/download';
import { getApiErrorMessage } from '@/utils/error';

const defaultResumeInput = `Name: {Full Name}
Title: {Current Role / Target Role}

Experience:
{List of bullet points describing work}

Projects:
{List of projects with brief descriptions}

Education:
{Degree, Institution, Year, optional GPA}

Achievements:
{Awards, recognitions, rankings, certifications}

Skills:
{List of skills}`;

export function ResumePage() {
  const initialState = useMemo(() => getResumePageState(defaultResumeInput), []);
  const [input, setInput] = useState(initialState.input);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [result, setResult] = useState<ResumeResponse | null>(initialState.result);
  const [history, setHistory] = useState<ResumeHistoryItem[]>(initialState.history);

  const pdfUrl = useMemo(() => result?.pdf_url || '', [result]);

  useEffect(() => {
    if (input === defaultResumeInput && !result?.pdf_url && history.length === 0) {
      return;
    }

    setResumePageState({
      input,
      result,
      history,
    });
  }, [history, input, result]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await generateResume(input);
      setResult(response);
      setHistory((currentHistory) =>
        appendResumeHistoryItem(currentHistory, {
          id: `${Date.now()}-${response.pdf_url}`,
          createdAt: new Date().toISOString(),
          input,
          pdfUrl: response.pdf_url,
          result: response,
        }),
      );
      toast.success('Resume generated successfully.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to generate resume.'));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDownload(url: string) {
    setIsDownloading(true);

    try {
      await downloadFromUrl(url, getFilenameFromUrl(url, 'resume.pdf'));
      toast.success('PDF downloaded.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to download the PDF.'));
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Resume Generator"
        description="Paste raw resume content, submit it to the API, and review the generated PDF inline."
      />

      <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
        <Card className="p-6">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <FormField
              label="Resume input"
              hint="Plain text"
            >
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Paste your resume draft here..."
                className="min-h-[420px] app-scrollbar"
                required
              />
            </FormField>

            <Button type="submit" fullWidth loading={isSubmitting}>
              Generate resume
            </Button>
          </form>
        </Card>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-ink">PDF Preview</h2>
              <p className="text-sm text-muted">Rendered output from the generated `pdf_url`.</p>
            </div>
            {result ? (
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  variant="secondary"
                  loading={isDownloading}
                  onClick={() => handleDownload(result.pdf_url)}
                >
                  <Download className="h-4 w-4" />
                  Download
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => window.open(result.pdf_url, '_blank', 'noopener,noreferrer')}
                >
                  <ExternalLink className="h-4 w-4" />
                  Open in new tab
                </Button>
              </div>
            ) : null}
          </div>

          <Card className="overflow-hidden">
            {isSubmitting ? (
              <div className="space-y-4 p-6">
                <Skeleton className="h-6 w-40" />
                <Skeleton className="h-[680px] w-full rounded-none" />
              </div>
            ) : pdfUrl ? (
              <iframe
                title="Generated resume PDF"
                src={pdfUrl}
                className="h-[760px] w-full bg-slate-50"
              />
            ) : (
              <div className="p-6">
                <EmptyState
                  icon={FileText}
                  title="No resume generated yet"
                  description="Submit raw resume content to render a PDF preview and expose download actions."
                />
              </div>
            )}
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center gap-2">
              <History className="h-4 w-4 text-slate-500" />
              <h3 className="text-sm font-semibold text-ink">PDF History</h3>
            </div>

            {history.length ? (
              <div className="space-y-3">
                {history.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setInput(item.input);
                      setResult(item.result);
                    }}
                    className="flex w-full items-start justify-between gap-4 rounded-lg border border-line px-4 py-3 text-left transition hover:border-slate-300 hover:bg-slate-50"
                  >
                    <div className="min-w-0 space-y-1">
                      <p className="truncate text-sm font-medium text-ink">
                        {getFilenameFromUrl(item.pdfUrl, 'resume.pdf')}
                      </p>
                      <p className="text-xs text-muted">
                        {item.input}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <div className="inline-flex items-center gap-1 text-xs text-slate-400">
                        <Clock3 className="h-3.5 w-3.5" />
                        {new Date(item.createdAt).toLocaleString()}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted">
                Generated PDF links will be saved here automatically.
              </p>
            )}
          </Card>
        </section>
      </div>
    </>
  );
}
