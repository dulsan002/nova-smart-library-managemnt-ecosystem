/**
 * LoginPage — advanced email + password login form with password toggle.
 */

import { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useMutation } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import {
  EnvelopeIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LOGIN } from '@/graphql/mutations/auth';
import { useAuthStore } from '@/stores/authStore';
import { ADMIN_ROLES } from '@/lib/constants';
import { extractGqlError } from '@/lib/utils';

const schema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuth = useAuthStore((s) => s.setAuth);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid, dirtyFields },
    watch,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: 'onChange',
  });

  const [login, { loading }] = useMutation(LOGIN);

  const emailValue = watch('email');
  const passwordValue = watch('password');

  const togglePassword = useCallback(() => setShowPassword((v) => !v), []);

  // Navigate after auth state is committed to the store
  useEffect(() => {
    if (!isAuthenticated || !user) return;

    const from = (location.state as { from?: { pathname: string } })?.from
      ?.pathname;

    if (from && from !== '/login' && from !== '/register' && from !== '/') {
      navigate(from, { replace: true });
      return;
    }

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
    <div className="animate-fade-in space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
          <ShieldCheckIcon className="h-3.5 w-3.5" />
          Secure Login
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-nova-text">
          Welcome back
        </h2>
        <p className="text-sm text-nova-text-secondary">
          Enter your credentials to access your NovaLib account
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Email field */}
        <div className="space-y-1.5">
          <Input
            label="Email Address"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
            leftIcon={
              <EnvelopeIcon
                className={`h-5 w-5 transition-colors duration-200 ${
                  dirtyFields.email && !errors.email
                    ? 'text-primary-500'
                    : ''
                }`}
              />
            }
            error={errors.email?.message}
            {...register('email')}
          />
        </div>

        {/* Password field with eye toggle */}
        <div className="space-y-1.5">
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder={showPassword ? 'Enter your password' : '••••••••'}
            autoComplete="current-password"
            leftIcon={
              <LockClosedIcon
                className={`h-5 w-5 transition-colors duration-200 ${
                  dirtyFields.password && !errors.password
                    ? 'text-primary-500'
                    : ''
                }`}
              />
            }
            rightIcon={
              <button
                type="button"
                onClick={togglePassword}
                className="rounded-md p-0.5 text-nova-text-muted transition-colors hover:text-nova-text focus:outline-none focus:ring-2 focus:ring-primary-500/40"
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            }
            error={errors.password?.message}
            {...register('password')}
          />
        </div>

        {/* Remember me + Forgot password row */}
        <div className="flex items-center justify-between">
          <label className="flex cursor-pointer items-center gap-2 select-none">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 rounded border-nova-border text-primary-600 focus:ring-primary-500/40 dark:bg-nova-surface"
            />
            <span className="text-sm text-nova-text-secondary">
              Remember me
            </span>
          </label>
          <Link
            to="/forgot-password"
            className="text-sm font-medium text-primary-600 transition-colors hover:text-primary-500 dark:text-primary-400"
          >
            Forgot password?
          </Link>
        </div>

        {/* Submit button */}
        <Button
          type="submit"
          fullWidth
          size="lg"
          isLoading={loading}
          className="group relative overflow-hidden shadow-lg shadow-primary-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-primary-500/30"
        >
          <span className="relative z-10 flex items-center gap-2">
            Sign In
            <ArrowRightIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
          </span>
        </Button>
      </form>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-nova-border" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-nova-bg px-3 text-nova-text-muted">
            New to NovaLib?
          </span>
        </div>
      </div>

      {/* Register link */}
      <Link
        to="/register"
        className="group flex w-full items-center justify-center gap-2 rounded-xl border-2 border-nova-border bg-transparent px-4 py-3 text-sm font-semibold text-nova-text transition-all duration-200 hover:border-primary-300 hover:bg-primary-50/50 dark:hover:border-primary-700 dark:hover:bg-primary-900/20"
      >
        Create an Account
        <ArrowRightIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
      </Link>

      {/* Security note */}
      <p className="flex items-center justify-center gap-1.5 text-center text-xs text-nova-text-muted">
        <LockClosedIcon className="h-3.5 w-3.5" />
        Protected by 256-bit SSL encryption
      </p>
    </div>
  );
}
