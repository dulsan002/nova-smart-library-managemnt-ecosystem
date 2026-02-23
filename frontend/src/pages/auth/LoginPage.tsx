/**
 * LoginPage — email + password login form.
 */

import { useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useMutation } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import { EnvelopeIcon, LockClosedIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LOGIN } from '@/graphql/mutations/auth';
import { useAuthStore } from '@/stores/authStore';
import { ADMIN_ROLES } from '@/lib/constants';
import { extractGqlError } from '@/lib/utils';

const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const [login, { loading }] = useMutation(LOGIN);

  // Navigate after auth state is committed to the store
  useEffect(() => {
    if (!isAuthenticated || !user) return;

    const from = (location.state as { from?: { pathname: string } })?.from
      ?.pathname;

    // If redirected from a protected page, go back there
    if (from && from !== '/login' && from !== '/register' && from !== '/') {
      navigate(from, { replace: true });
      return;
    }

    // Role-based redirect to respective panel
    if (ADMIN_ROLES.includes(user.role)) {
      navigate('/admin/dashboard', { replace: true });
    } else {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, user, navigate, location.state]);

  async function onSubmit(data: FormValues) {
    try {
      const { data: result } = await login({
        variables: { input: { email: data.email, password: data.password } },
      });

      const payload = result?.login;
      if (!payload?.tokens?.accessToken) {
        toast.error('Invalid credentials');
        return;
      }

      const { tokens, user: loginUser } = payload;

      // Store auth data — navigation is handled by the useEffect above
      if (loginUser) {
        setAuth(
          {
            id: loginUser.id,
            email: loginUser.email,
            firstName: loginUser.firstName,
            lastName: loginUser.lastName,
            role: loginUser.role,
            isVerified: loginUser.isVerified,
            avatarUrl: loginUser.avatarUrl,
          },
          tokens.accessToken,
          tokens.refreshToken,
        );
      }

      toast.success('Welcome back!');
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  }

  return (
    <div className="animate-fade-in">
      <h2 className="text-2xl font-bold text-nova-text">Welcome back</h2>
      <p className="mt-2 text-sm text-nova-text-secondary">
        Sign in to your NovaLib account
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
        <Input
          label="Email"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          leftIcon={<EnvelopeIcon className="h-5 w-5" />}
          error={errors.email?.message}
          {...register('email')}
        />

        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          leftIcon={<LockClosedIcon className="h-5 w-5" />}
          error={errors.password?.message}
          {...register('password')}
        />

        <Button type="submit" fullWidth isLoading={loading}>
          Sign In
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-nova-text-secondary">
        Don&apos;t have an account?{' '}
        <Link
          to="/register"
          className="font-semibold text-primary-600 hover:text-primary-500"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}
