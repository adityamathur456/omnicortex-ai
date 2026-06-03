import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import { FileImage, Upload } from 'lucide-react';
import toast from 'react-hot-toast';
import { analyzeMedical } from '@/api/medical';
import { EmptyState } from '@/components/empty-state';
import { FormField } from '@/components/form-field';
import { PageHeader } from '@/components/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { medicalModalities } from '@/utils/constants';
import { getApiErrorMessage } from '@/utils/error';
import type { MedicalResponse } from '@/types';

export function MedicalPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modalityHint, setModalityHint] = useState('MRI');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<MedicalResponse | null>(null);

  const localPreview = useMemo(() => {
    if (!selectedFile) {
      return '';
    }

    return URL.createObjectURL(selectedFile);
  }, [selectedFile]);

  useEffect(() => {
    return () => {
      if (localPreview) {
        URL.revokeObjectURL(localPreview);
      }
    };
  }, [localPreview]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] || null;
    setSelectedFile(file);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      toast.error('Select a clinical image or report before submitting.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await analyzeMedical(selectedFile, modalityHint);
      setResult(response);
      toast.success('Medical analysis completed.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to analyze the uploaded file.'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Medical Analyzer"
        description="Upload a clinical image or report, set a modality hint, and inspect the structured findings returned by the API."
      />

      <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
        <Card className="p-6">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <FormField label="Clinical file" hint="PNG, JPG, JPEG, WEBP">
              <label className="flex min-h-[180px] cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-line bg-slate-50 px-4 py-8 text-center transition hover:border-slate-300 hover:bg-slate-100">
                <Upload className="mb-3 h-6 w-6 text-slate-500" />
                <span className="text-sm font-medium text-ink">
                  {selectedFile ? selectedFile.name : 'Choose a file'}
                </span>
                <span className="mt-1 text-xs text-muted">
                  Upload radiology scans, reports, or related imagery
                </span>
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.webp"
                  className="sr-only"
                  onChange={handleFileChange}
                />
              </label>
            </FormField>

            <FormField label="Modality hint">
              <Select
                value={modalityHint}
                onChange={(event) => setModalityHint(event.target.value)}
              >
                {medicalModalities.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </Select>
            </FormField>

            <Button type="submit" fullWidth loading={isSubmitting}>
              Analyze file
            </Button>
          </form>
        </Card>

        <section className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-ink">Analysis Result</h2>
            <p className="text-sm text-muted">Structured output from the medical analysis endpoint.</p>
          </div>

          {isSubmitting ? (
            <Card className="space-y-5 p-6">
              <Skeleton className="aspect-[16/9] w-full" />
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-16 w-full" />
            </Card>
          ) : result ? (
            <Card className="overflow-hidden">
              <div className="grid gap-0 lg:grid-cols-[0.95fr_1.05fr]">
                <div className="border-b border-line bg-slate-50 p-4 lg:border-b-0 lg:border-r">
                  <div className="overflow-hidden rounded-lg border border-line bg-white">
                    <img
                      src={result.image_url || localPreview}
                      alt="Uploaded medical reference"
                      className="aspect-[4/3] w-full object-cover"
                    />
                  </div>
                </div>

                <div className="space-y-5 p-6">
                  <div className="flex flex-wrap items-center gap-3">
                    <Badge tone="success">{result.modality || modalityHint}</Badge>
                    <Badge tone="warning">{result.confidence || 'Confidence pending'}</Badge>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Findings
                    </h3>
                    <p className="text-sm text-slate-700">{result.findings}</p>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Possible Conditions
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {result.possible_conditions?.length ? (
                        result.possible_conditions.map((condition) => (
                          <Badge key={condition}>{condition}</Badge>
                        ))
                      ) : (
                        <p className="text-sm text-muted">No possible conditions returned.</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-sm font-semibold uppercase tracking-[0.08em] text-slate-500">
                      Recommendation
                    </h3>
                    <p className="text-sm text-slate-700">{result.recommendation}</p>
                  </div>

                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                    <p className="text-sm text-amber-800">{result.disclaimer}</p>
                  </div>
                </div>
              </div>
            </Card>
          ) : (
            <EmptyState
              icon={FileImage}
              title="No analysis yet"
              description="Upload a supported file and submit the form to inspect modality, findings, conditions, confidence, and recommendation."
            />
          )}
        </section>
      </div>
    </>
  );
}
