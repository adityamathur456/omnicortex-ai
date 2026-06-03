import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { AuthShell } from '@/components/auth-shell';
import { FormField } from '@/components/form-field';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/store/auth-store';
import { getApiErrorMessage } from '@/utils/error';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      await login({ email, password });
      toast.success('Logged in successfully.');
      const nextPath =
        typeof (location.state as { from?: unknown } | null)?.from === 'string'
          ? (location.state as { from: string }).from
          : '/dashboard';
      navigate(nextPath, { replace: true });
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to login.'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Sign in"
      subtitle="Access your Omnicortex AI workspace."
      sideTitle="A multimodal AI platform built to expand with new tools and agentic workflows."
      sideText="Omnicortex AI is in active production growth, designed to keep evolving as new tools, automations, and intelligent workflows are added."
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <FormField label="Email">
          <Input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@company.com"
            required
          />
        </FormField>

        <FormField label="Password">
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            required
          />
        </FormField>

        <Button type="submit" fullWidth loading={isSubmitting}>
          Continue
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted">
        Need an account?{' '}
        <Link className="font-medium text-ink underline-offset-4 hover:underline" to="/register">
          Create one
        </Link>
      </p>
    </AuthShell>
  );
}
