/**
 * ForgotPasswordPage — 3-step OTP password reset flow.
 *
 * Step 1: Enter email → get masked email hint + session token
 * Step 2: Enter 6-digit OTP sent to email
 * Step 3: Set new password
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@apollo/client';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import toast from 'react-hot-toast';
import {
  EnvelopeIcon,
  ArrowLeftIcon,
  PaperAirplaneIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowRightIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  REQUEST_PASSWORD_RESET,
  VERIFY_RESET_OTP,
  CONFIRM_PASSWORD_RESET,
} from '@/graphql/mutations/auth';
import { extractGqlError } from '@/lib/utils';

/* ── Step indicator ── */
function StepIndicator({ current }: { current: number }) {
  const steps = [
    { num: 1, label: 'Email' },
    { num: 2, label: 'Verify' },
    { num: 3, label: 'New Password' },
  ];
  return (
    <div className="mb-8 flex items-center justify-center gap-2">
      {steps.map((step, i) => (
        <div key={step.num} className="flex items-center gap-2">
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-all duration-300 ${
              current > step.num
                ? 'bg-green-500 text-white shadow-lg shadow-green-500/30'
                : current === step.num
                  ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/30 ring-4 ring-primary-500/20'
                  : 'bg-nova-surface text-nova-text-secondary border border-nova-border'
            }`}
          >
            {current > step.num ? (
              <CheckCircleIcon className="h-4 w-4" />
            ) : (
              step.num
            )}
          </div>
          <span
            className={`hidden text-xs font-medium sm:block ${
              current >= step.num ? 'text-nova-text' : 'text-nova-text-secondary'
            }`}
          >
            {step.label}
          </span>
          {i < steps.length - 1 && (
            <div
              className={`mx-1 h-0.5 w-6 rounded transition-colors ${
                current > step.num ? 'bg-green-500' : 'bg-nova-border'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

/* ── OTP input (6 boxes) ── */
function OtpInput({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (val: string) => void;
  disabled?: boolean;
}) {
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);
  const digits = value.padEnd(6, ' ').split('').slice(0, 6);

  const handleChange = useCallback(
    (index: number, char: string) => {
      if (!/^\d?$/.test(char)) return;
      const arr = digits.slice();
      arr[index] = char;
      const next = arr.join('');
      onChange(next.replace(/ /g, ''));
      if (char && index < 5) {
        inputsRef.current[index + 1]?.focus();
      }
    },
    [digits, onChange],
  );

  const handleKeyDown = useCallback(
    (index: number, e: React.KeyboardEvent) => {
      if (e.key === 'Backspace' && !digits[index] && index > 0) {
        inputsRef.current[index - 1]?.focus();
      }
    },
    [digits],
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      e.preventDefault();
      const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
      onChange(pasted);
      const focusIdx = Math.min(pasted.length, 5);
      inputsRef.current[focusIdx]?.focus();
    },
    [onChange],
  );

  return (
    <div className="flex items-center justify-center gap-3" onPaste={handlePaste}>
      {digits.map((d, i) => (
        <input
          key={i}
          ref={el => { inputsRef.current[i] = el; }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={d === ' ' ? '' : d}
          disabled={disabled}
          onChange={e => handleChange(i, e.target.value)}
          onKeyDown={e => handleKeyDown(i, e)}
          style={{
            width: '3rem',
            height: '3.5rem',
            border: d && d !== ' ' ? '2px solid #6366f1' : '2px solid #d1d5db',
            borderRadius: '0.75rem',
            textAlign: 'center' as const,
            fontSize: '1.25rem',
            fontWeight: 700,
            backgroundColor: d && d !== ' ' ? '#eef2ff' : '#ffffff',
            color: '#111827',
            outline: 'none',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
          }}
          className={`transition-all duration-200 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20 ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
        />
      ))}
    </div>
  );
}

/* ── Password strength ── */
function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: '8+ characters', met: password.length >= 8 },
    { label: 'Uppercase letter', met: /[A-Z]/.test(password) },
    { label: 'Lowercase letter', met: /[a-z]/.test(password) },
    { label: 'Number', met: /\d/.test(password) },
    { label: 'Special character', met: /[!@#$%^&*(),.?":{}|<>]/.test(password) },
  ];
  const score = checks.filter(c => c.met).length;
  const pct = (score / checks.length) * 100;
  const color =
    score <= 1 ? 'bg-red-500' : score <= 2 ? 'bg-orange-500' : score <= 3 ? 'bg-yellow-500' : score <= 4 ? 'bg-blue-500' : 'bg-green-500';
  const label =
    score <= 1 ? 'Very weak' : score <= 2 ? 'Weak' : score <= 3 ? 'Fair' : score <= 4 ? 'Strong' : 'Very strong';

  if (!password) return null;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-nova-text-secondary">Password strength</span>
        <span className={`font-medium ${score >= 4 ? 'text-green-600' : score >= 3 ? 'text-yellow-600' : 'text-red-600'}`}>
          {label}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-nova-border">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="grid grid-cols-2 gap-1">
        {checks.map(c => (
          <div key={c.label} className="flex items-center gap-1.5 text-xs">
            <div className={`h-1.5 w-1.5 rounded-full ${c.met ? 'bg-green-500' : 'bg-nova-border'}`} />
            <span className={c.met ? 'text-green-600 dark:text-green-400' : 'text-nova-text-secondary'}>
              {c.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main component ── */
const emailSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [sessionToken, setSessionToken] = useState('');
  const [maskedEmail, setMaskedEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [showConfirmPw, setShowConfirmPw] = useState(false);
  const [done, setDone] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ email: string }>({ resolver: zodResolver(emailSchema), mode: 'onChange' });

  const [requestReset, { loading: requesting }] = useMutation(REQUEST_PASSWORD_RESET);
  const [verifyOtp, { loading: verifying }] = useMutation(VERIFY_RESET_OTP);
  const [confirmReset, { loading: confirming }] = useMutation(CONFIRM_PASSWORD_RESET);

  // Countdown timer for resend
  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  /* Step 1 — Submit email */
  const onEmailSubmit = async (data: { email: string }) => {
    try {
      const { data: result } = await requestReset({ variables: { email: data.email } });
      const payload = result?.requestPasswordReset;
      if (payload?.success) {
        setSessionToken(payload.sessionToken);
        setMaskedEmail(payload.maskedEmail);
        setStep(2);
        setCountdown(60);
        toast.success('Verification code sent!');
      } else {
        toast.error(payload?.message || 'Account not found.');
      }
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  };

  /* Step 2 — Verify OTP */
  const onOtpSubmit = async () => {
    if (otp.length !== 6) {
      toast.error('Please enter the full 6-digit code.');
      return;
    }
    try {
      const { data: result } = await verifyOtp({
        variables: { sessionToken, otp },
      });
      if (result?.verifyResetOtp?.success) {
        setStep(3);
        toast.success('Code verified!');
      }
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  };

  /* Step 3 — Set new password */
  const onPasswordSubmit = async () => {
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }
    try {
      const { data: result } = await confirmReset({
        variables: { sessionToken, newPassword },
      });
      if (result?.confirmPasswordReset?.success) {
        setDone(true);
        toast.success('Password reset successfully!');
      }
    } catch (err) {
      toast.error(extractGqlError(err));
    }
  };

  /* Resend OTP */
  const handleResend = () => {
    setStep(1);
    setOtp('');
    toast('Please enter your email again to resend the code.', { icon: '📧' });
  };

  /* ── Success screen ── */
  if (done) {
    return (
      <div className="animate-fade-in space-y-6 text-center">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-green-400 to-emerald-500 shadow-lg shadow-green-500/30">
          <CheckCircleIcon className="h-10 w-10 text-white" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-nova-text">
            Password Reset Complete!
          </h2>
          <p className="text-sm text-nova-text-secondary">
            Your password has been changed successfully. You can now sign in with your new password.
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
            <ArrowRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </span>
        </Button>
      </div>
    );
  }

  return (
    <div className="animate-fade-in space-y-6">
      <StepIndicator current={step} />

      {/* ═══════════════ Step 1: Enter Email ═══════════════ */}
      {step === 1 && (
        <div className="space-y-6">
          <div className="space-y-2">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
              <ShieldCheckIcon className="h-3.5 w-3.5" />
              Account Recovery
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-nova-text">Forgot password?</h2>
            <p className="text-sm text-nova-text-secondary">
              Enter your registered email address and we&apos;ll send you a 6-digit verification code.
            </p>
          </div>

          <form onSubmit={handleSubmit(onEmailSubmit)} className="space-y-5">
            <Input
              label="Email Address"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              leftIcon={<EnvelopeIcon className="h-5 w-5" />}
              error={errors.email?.message}
              {...register('email')}
            />

            <Button
              type="submit"
              fullWidth
              size="lg"
              isLoading={requesting}
              className="group relative overflow-hidden shadow-lg shadow-primary-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-primary-500/30"
            >
              <span className="relative z-10 flex items-center gap-2">
                Send Verification Code
                <PaperAirplaneIcon className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </span>
            </Button>
          </form>

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
      )}

      {/* ═══════════════ Step 2: Enter OTP ═══════════════ */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="space-y-2 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
              <EnvelopeIcon className="h-7 w-7 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-nova-text">Check your email</h2>
            <p className="text-sm text-nova-text-secondary">
              We sent a 6-digit verification code to
            </p>
            <p className="inline-flex items-center gap-2 rounded-lg bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
              <EnvelopeIcon className="h-4 w-4" />
              {maskedEmail}
            </p>
          </div>

          <div className="space-y-4">
            <label className="block text-center text-sm font-medium text-nova-text">
              Enter verification code
            </label>
            <OtpInput value={otp} onChange={setOtp} disabled={verifying} />
          </div>

          <Button
            fullWidth
            size="lg"
            onClick={onOtpSubmit}
            isLoading={verifying}
            disabled={otp.length !== 6 || verifying}
            className="group shadow-lg shadow-primary-500/25"
          >
            <span className="flex items-center gap-2">
              Verify Code
              <ArrowRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Button>

          <div className="space-y-3 text-center">
            <div className="rounded-xl border border-nova-border bg-nova-surface p-3 text-xs text-nova-text-secondary">
              <p>
                Didn&apos;t receive the code? Check your spam folder, or{' '}
                {countdown > 0 ? (
                  <span className="text-nova-text">resend in {countdown}s</span>
                ) : (
                  <button
                    onClick={handleResend}
                    className="font-medium text-primary-600 hover:text-primary-500"
                  >
                    resend code
                  </button>
                )}
              </p>
            </div>
            <button
              onClick={() => { setStep(1); setOtp(''); }}
              className="inline-flex items-center gap-1 text-xs font-medium text-nova-text-secondary hover:text-nova-text"
            >
              <ArrowLeftIcon className="h-3 w-3" />
              Use a different email
            </button>
          </div>
        </div>
      )}

      {/* ═══════════════ Step 3: New Password ═══════════════ */}
      {step === 3 && (
        <div className="space-y-6">
          <div className="space-y-2 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
              <LockClosedIcon className="h-7 w-7 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-nova-text">Set new password</h2>
            <p className="text-sm text-nova-text-secondary">
              Your identity has been verified. Choose a strong new password.
            </p>
          </div>

          <div className="space-y-4">
            {/* New Password */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-nova-text">New Password</label>
              <div className="relative">
                <LockClosedIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-nova-text-secondary" />
                <input
                  type={showPw ? 'text' : 'password'}
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  className="w-full rounded-xl border border-nova-border bg-nova-surface py-3 pl-10 pr-12 text-sm text-nova-text focus:border-primary-500 focus:outline-none focus:ring-4 focus:ring-primary-500/20"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-nova-text-secondary hover:text-nova-text"
                >
                  {showPw ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                </button>
              </div>
              <PasswordStrength password={newPassword} />
            </div>

            {/* Confirm Password */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-nova-text">Confirm Password</label>
              <div className="relative">
                <LockClosedIcon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-nova-text-secondary" />
                <input
                  type={showConfirmPw ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  className={`w-full rounded-xl border bg-nova-surface py-3 pl-10 pr-12 text-sm text-nova-text focus:outline-none focus:ring-4 ${
                    confirmPassword && confirmPassword !== newPassword
                      ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20'
                      : confirmPassword && confirmPassword === newPassword
                        ? 'border-green-400 focus:border-green-500 focus:ring-green-500/20'
                        : 'border-nova-border focus:border-primary-500 focus:ring-primary-500/20'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPw(!showConfirmPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-nova-text-secondary hover:text-nova-text"
                >
                  {showConfirmPw ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                </button>
              </div>
              {confirmPassword && confirmPassword !== newPassword && (
                <p className="mt-1 flex items-center gap-1 text-xs text-red-500">
                  <ExclamationTriangleIcon className="h-3.5 w-3.5" />
                  Passwords do not match
                </p>
              )}
              {confirmPassword && confirmPassword === newPassword && (
                <p className="mt-1 flex items-center gap-1 text-xs text-green-600">
                  <CheckCircleIcon className="h-3.5 w-3.5" />
                  Passwords match
                </p>
              )}
            </div>
          </div>

          <Button
            fullWidth
            size="lg"
            onClick={onPasswordSubmit}
            isLoading={confirming}
            disabled={!newPassword || newPassword.length < 8 || newPassword !== confirmPassword || confirming}
            className="group shadow-lg shadow-primary-500/25"
          >
            <span className="flex items-center gap-2">
              Reset Password
              <CheckCircleIcon className="h-4 w-4" />
            </span>
          </Button>
        </div>
      )}
    </div>
  );
}
