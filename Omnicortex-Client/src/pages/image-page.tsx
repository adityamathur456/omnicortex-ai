import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Clock3, Download, History, Image as ImageIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import { generateImage } from '@/api/image';
import { EmptyState } from '@/components/empty-state';
import { FormField } from '@/components/form-field';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  appendImageHistoryItem,
  getImagePageState,
  setImagePageState,
} from '@/store/generation-history';
import type { ImageHistoryItem } from '@/types';
import { imageModes } from '@/utils/constants';
import { downloadFromUrl, getFilenameFromUrl } from '@/utils/download';
import { getApiErrorMessage } from '@/utils/error';

const defaultPrompt =
  'A cinematic studio portrait of an AI founder at a modern workspace.';

export function ImagePage() {
  const initialState = useMemo(
    () => getImagePageState(defaultPrompt, 'portrait', 4),
    [],
  );
  const [prompt, setPrompt] = useState(initialState.prompt);
  const [mode, setMode] = useState(initialState.mode);
  const [steps, setSteps] = useState(initialState.steps);
  const [imageUrl, setImageUrl] = useState(initialState.imageUrl);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [history, setHistory] = useState<ImageHistoryItem[]>(initialState.history);

  useEffect(() => {
    setImagePageState({
      prompt,
      mode,
      steps,
      imageUrl,
      history,
    });
  }, [history, imageUrl, mode, prompt, steps]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await generateImage({
        prompt,
        mode,
        person_generation: 'allow_adult',
        steps,
      });
      setImageUrl(response.url);
      setHistory((currentHistory) =>
        appendImageHistoryItem(currentHistory, {
          id: `${Date.now()}-${response.url}`,
          createdAt: new Date().toISOString(),
          prompt,
          mode,
          steps,
          imageUrl: response.url,
        }),
      );
      toast.success('Image generated successfully.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to generate image.'));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDownload(url: string) {
    setIsDownloading(true);

    try {
      await downloadFromUrl(url, getFilenameFromUrl(url, 'generated-image.png'));
      toast.success('Image downloaded.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to download the image.'));
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Image Generator"
        description="Submit prompt-based generation jobs and review the rendered result with a direct download action."
      />

      <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
        <Card className="p-6">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <FormField label="Prompt">
              <Input
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Describe the image you want to generate"
                required
              />
            </FormField>

            <FormField label="Mode">
              <Select value={mode} onChange={(event) => setMode(event.target.value)}>
                {imageModes.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </Select>
            </FormField>

            <FormField label="Steps" hint="Inference steps">
              <Input
                type="number"
                min={1}
                max={20}
                value={steps}
                onChange={(event) => setSteps(Number(event.target.value) || 1)}
                required
              />
            </FormField>

            <Button type="submit" fullWidth loading={isSubmitting}>
              Generate image
            </Button>
          </form>
        </Card>

        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-ink">Output Preview</h2>
              <p className="text-sm text-muted">Rendered image returned by the generation endpoint.</p>
            </div>
            {imageUrl ? (
              <Button
                type="button"
                variant="secondary"
                loading={isDownloading}
                onClick={() => handleDownload(imageUrl)}
              >
                <Download className="h-4 w-4" />
                Download
              </Button>
            ) : null}
          </div>

          <Card className="overflow-hidden p-6">
            {isSubmitting ? (
              <div className="space-y-4">
                <Skeleton className="h-6 w-40" />
                <Skeleton className="aspect-[4/3] w-full" />
              </div>
            ) : imageUrl ? (
              <div className="overflow-hidden rounded-lg border border-line bg-slate-50">
                <img
                  src={imageUrl}
                  alt="Generated preview"
                  className="aspect-[4/3] w-full object-cover"
                />
              </div>
            ) : (
              <EmptyState
                icon={ImageIcon}
                title="No image generated yet"
                description="Submit a prompt to render an image preview and a downloadable output."
              />
            )}
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center gap-2">
              <History className="h-4 w-4 text-slate-500" />
              <h3 className="text-sm font-semibold text-ink">Image History</h3>
            </div>

            {history.length ? (
              <div className="space-y-3">
                {history.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setPrompt(item.prompt);
                      setMode(item.mode);
                      setSteps(item.steps);
                      setImageUrl(item.imageUrl);
                    }}
                    className="flex w-full items-start justify-between gap-4 rounded-lg border border-line px-4 py-3 text-left transition hover:border-slate-300 hover:bg-slate-50"
                  >
                    <div className="min-w-0 space-y-1">
                      <p className="truncate text-sm font-medium text-ink">
                        {item.prompt}
                      </p>
                      <p className="text-xs text-muted">
                        {item.mode} · {item.steps} steps
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
                Generated image links will be saved here automatically.
              </p>
            )}
          </Card>
        </section>
      </div>
    </>
  );
}
