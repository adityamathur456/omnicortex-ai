import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { AuthShell } from '@/components/auth-shell';
import { FormField } from '@/components/form-field';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/store/auth-store';
import { getApiErrorMessage } from '@/utils/error';

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);

    try {
      await register({
        full_name: fullName,
        email,
        password,
      });
      toast.success('Registration complete. You can sign in now.');
      navigate('/login', { replace: true });
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Unable to register.'));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Create account"
      subtitle="Set up your Omnicortex AI workspace."
      sideTitle="A multimodal agent that works across text, vision, and clinical context."
      sideText="Omnicortex AI brings creation, analysis, and decision support into one evolving workspace where every new tool makes the system sharper and more capable."
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <FormField label="Full name">
          <Input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Aditya Sharma"
            required
          />
        </FormField>

        <FormField label="Email">
          <Input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@company.com"
            required
          />
        </FormField>

        <FormField label="Password" hint="Use at least 8 characters">
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Create a password"
            minLength={8}
            required
          />
        </FormField>

        <Button type="submit" fullWidth loading={isSubmitting}>
          Create account
        </Button>
      </form>

      <p className="mt-6 text-sm text-muted">
        Already registered?{' '}
        <Link className="font-medium text-ink underline-offset-4 hover:underline" to="/login">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
