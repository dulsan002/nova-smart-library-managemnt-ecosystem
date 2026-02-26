/**
 * ResetPasswordPage — set a new password using a reset token.
 */

import { useState, useCallback } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import {
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  KeyIcon,
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { CONFIRM_PASSWORD_RESET } from '@/graphql/mutations/auth';
import { extractGqlError } from '@/lib/utils';

const schema = z
  .object({
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Must contain at least one number'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type FormValues = z.infer<typeof schema>;

/** Helper: strength score 0-4 */
function passwordStrength(pw: string): number {
  let s = 0;
  if (pw.length >= 8) s++;
  if (/[A-Z]/.test(pw)) s++;
  if (/[a-z]/.test(pw)) s++;
  if (/[0-9]/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return Math.min(s, 4);
}

const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
const strengthColors = [
  'bg-gray-200 dark:bg-gray-700',
  'bg-red-500',
  'bg-amber-500',
  'bg-blue-500',
  'bg-green-500',
];

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [done, setDone] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), mode: 'onChange' });

  const [confirmReset, { loading }] = useMutation(CONFIRM_PASSWORD_RESET);
  const passwordValue = watch('password', '');
  const strength = passwordStrength(passwordValue);

  const togglePw = useCallback(() => setShowPassword((v) => !v), []);
  const toggleConfirm = useCallback(() => setShowConfirm((v) => !v), []);

  async function onSubmit(data: FormValues) {
    try {
      const { data: result } = await confirmReset({
        variables: { token, newPassword: data.password },
      });

      if (result?.confirmPasswordReset?.success) {
        setDone(true);
        toast.success('Password reset successfully!');
      }
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  }

  // ── No token ──
  if (!token && !done) {
    return (
      <div className="animate-fade-in space-y-6 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
          <ShieldCheckIcon className="h-8 w-8 text-red-600 dark:text-red-400" />
        </div>
        <h2 className="text-2xl font-bold text-nova-text">Invalid Reset Link</h2>
        <p className="text-sm text-nova-text-secondary">
          This password reset link is invalid or has expired.
          Please request a new one.
        </p>
        <div className="flex flex-col gap-3">
          <Button fullWidth onClick={() => navigate('/forgot-password')}>
            Request New Link
          </Button>
          <Link
            to="/login"
            className="inline-flex items-center justify-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Sign In
          </Link>
        </div>
      </div>
    );
  }

  // ── Success state ──
  if (done) {
    return (
      <div className="animate-fade-in space-y-6 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
          <CheckCircleIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-nova-text">
            Password Reset Complete
          </h2>
          <p className="text-sm text-nova-text-secondary">
            Your password has been changed successfully. You can now sign in with
            your new password.
          </p>
        </div>
        <Button
          fullWidth
          size="lg"
          onClick={() => navigate('/login')}
          className="group shadow-lg shadow-primary-500/25"
        >
          <span className="flex items-center gap-2">
            Continue to Sign In
            <ArrowRightIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
          </span>
        </Button>
      </div>
    );
  }

  // ── Reset form ──
  return (
    <div className="animate-fade-in space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
          <KeyIcon className="h-3.5 w-3.5" />
          New Password
        </div>
        <h2 className="text-3xl font-bold tracking-tight text-nova-text">
          Set new password
        </h2>
        <p className="text-sm text-nova-text-secondary">
          Choose a strong password that you haven&apos;t used before.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* New password */}
        <div className="space-y-2">
          <Input
            label="New Password"
            type={showPassword ? 'text' : 'password'}
            placeholder={showPassword ? 'Enter new password' : '••••••••'}
            autoComplete="new-password"
            leftIcon={<LockClosedIcon className="h-5 w-5" />}
            rightIcon={
              <button
                type="button"
                onClick={togglePw}
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

          {/* Strength meter */}
          {passwordValue.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex gap-1">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${
                      i <= strength
                        ? strengthColors[strength]
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  />
                ))}
              </div>
              <p className="text-xs text-nova-text-muted">
                Strength:{' '}
                <span
                  className={`font-medium ${
                    strength <= 1
                      ? 'text-red-500'
                      : strength === 2
                        ? 'text-amber-500'
                        : strength === 3
                          ? 'text-blue-500'
                          : 'text-green-500'
                  }`}
                >
                  {strengthLabels[strength]}
                </span>
              </p>
            </div>
          )}
        </div>

        {/* Confirm password */}
        <Input
          label="Confirm Password"
          type={showConfirm ? 'text' : 'password'}
          placeholder={showConfirm ? 'Re-enter password' : '••••••••'}
          autoComplete="new-password"
          leftIcon={<LockClosedIcon className="h-5 w-5" />}
          rightIcon={
            <button
              type="button"
              onClick={toggleConfirm}
              className="rounded-md p-0.5 text-nova-text-muted transition-colors hover:text-nova-text focus:outline-none focus:ring-2 focus:ring-primary-500/40"
              tabIndex={-1}
              aria-label={showConfirm ? 'Hide password' : 'Show password'}
            >
              {showConfirm ? (
                <EyeSlashIcon className="h-5 w-5" />
              ) : (
                <EyeIcon className="h-5 w-5" />
              )}
            </button>
          }
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />

        {/* Password requirements */}
        <div className="rounded-xl border border-nova-border bg-nova-surface p-4">
          <p className="mb-2 text-xs font-medium text-nova-text">
            Password requirements:
          </p>
          <ul className="space-y-1 text-xs text-nova-text-muted">
            {[
              { label: 'At least 8 characters', met: passwordValue.length >= 8 },
              { label: 'One uppercase letter', met: /[A-Z]/.test(passwordValue) },
              { label: 'One lowercase letter', met: /[a-z]/.test(passwordValue) },
              { label: 'One number', met: /[0-9]/.test(passwordValue) },
            ].map((req) => (
              <li key={req.label} className="flex items-center gap-2">
                <span
                  className={`inline-block h-1.5 w-1.5 rounded-full transition-colors ${
                    req.met ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                />
                <span className={req.met ? 'text-green-600 dark:text-green-400' : ''}>
                  {req.label}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <Button
          type="submit"
          fullWidth
          size="lg"
          isLoading={loading}
          className="group relative overflow-hidden shadow-lg shadow-primary-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-primary-500/30"
        >
          <span className="relative z-10 flex items-center gap-2">
            Reset Password
            <ArrowRightIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
          </span>
        </Button>
      </form>

      {/* Back to login */}
      <div className="text-center">
        <Link
          to="/login"
          className="inline-flex items-center gap-2 text-sm font-medium text-primary-600 transition-colors hover:text-primary-500 dark:text-primary-400"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to Sign In
        </Link>
      </div>
    </div>
  );
}
